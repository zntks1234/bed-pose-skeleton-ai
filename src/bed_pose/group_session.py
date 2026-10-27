"""Two-input lifecycle, durable references and post-recording receive-time alignment."""
from pathlib import Path
import time
import uuid
from .io_utils import atomic_json, file_hash, load_json
from .live_recording import verify_live


class MeasurementGroup:
    def __init__(self, members, root, max_skew_ns=None):
        self.members = list(members)
        self.id = uuid.uuid4().hex
        self.directory = Path(root)/'groups'/self.id
        self.directory.mkdir(parents=True, exist_ok=False)
        self.data = {'schema_version':'group-0.1-draft', 'group_id':self.id,
                     'phase':'starting', 'ledger_complete':False,
                     'alignment_max_skew_ns':str(max_skew_ns) if max_skew_ns is not None else None,
                     'requested_start_perf_counter_ns':str(time.perf_counter_ns()),
                     'requested_stop_perf_counter_ns':None,
                     'members':[{'input_id':s.id,'title':s.title,'run_directory':None,
                                 'started_ack_perf_counter_ns':None,'stopped_ack_perf_counter_ns':None} for s in members],
                     'errors':[], 'alignment_status':'pending_until_stop' if max_skew_ns is not None else 'not_implemented',
                     'target_association_status':'not_configured',
                     'posture_prediction':{'status':'not_implemented','label':None}}
        self.finished, self.failed = False, False
        self.save()

    def save(self):
        atomic_json(self.directory/'manifest.json', self.data)

    def start(self):
        for session in self.members:
            session.state['pending']='start'
            session.worker.submit('start')

    def stop(self, close_inputs=False):
        if self.finished:return
        self.data['phase']='stopping'
        if self.data['requested_stop_perf_counter_ns'] is None:
            self.data['requested_stop_perf_counter_ns']=str(time.perf_counter_ns())
        self.save()
        for session in self.members:
            if close_inputs:
                session.worker.request_close()
            elif not session.state['closed']:
                session.state['pending']='stop'
                session.worker.submit('stop')

    def message(self, session, kind, value):
        if self.finished:return
        member=next(m for m in self.data['members'] if m['input_id']==session.id)
        if kind=='started':
            member['run_directory']=value['directory']
            member['started_ack_perf_counter_ns']=str(time.perf_counter_ns())
            if all(m['run_directory'] for m in self.data['members']) and self.data['phase']=='starting':
                self.data['phase']='recording'
            self.save()
        elif kind=='stopped':
            member['stopped_ack_perf_counter_ns']=str(time.perf_counter_ns())
            if value['manifest']['run_status']!='succeeded':
                self.fail('MEMBER_RECORDING_FAILED',session.id)
            self.save()
        elif kind in ('error','command_rejected'):
            self.fail('MEMBER_'+kind.upper(),session.id)
        elif kind in ('eof','closed') and self.data['phase'] in ('starting','recording'):
            # One input ending also ends the partner interval.
            self.stop(close_inputs=True)

    def fail(self, code, input_id=None):
        self.failed=True
        self.data['errors'].append({'code':code,'input_id':input_id})
        self.stop(close_inputs=True)

    def tick(self):
        if self.finished:return
        done=all(m['stopped_ack_perf_counter_ns'] is not None or s.state['closed']
                 for s,m in zip(self.members,self.data['members']))
        if not done:return
        for session,member in zip(self.members,self.data['members']):
            directory=member['run_directory']
            if directory is None:
                self.failed=True
                self.data['errors'].append({'code':'MEMBER_NOT_STARTED','input_id':session.id})
                continue
            try:
                summary=verify_live(directory)
                manifest=load_json(Path(directory)/'manifest.json')
                member['record_validation']=summary
                member['manifest_sha256']=file_hash(Path(directory)/'manifest.json')
                member['timing']={k:manifest[k] for k in ('clock_id','clock_origin_perf_counter_ns','started_ns','finished_ns','first_stream_frame_id','recorded_frames')}
                if summary['run_status']!='succeeded':self.failed=True
            except Exception as exc:
                self.failed=True
                self.data['errors'].append({'code':'MEMBER_VERIFICATION_FAILED','input_id':session.id,'exception_type':type(exc).__name__})
        if not self.failed and self.data['alignment_max_skew_ns'] is not None:
            try:
                from .time_alignment import align_group
                self.data['alignment']=align_group(self.data['members'],self.directory,int(self.data['alignment_max_skew_ns']))
                self.data['alignment_status']=self.data['alignment']['status']
            except Exception as exc:
                self.failed=True
                self.data['alignment_status']='failed'
                self.data['errors'].append({'code':'ALIGNMENT_FAILED','exception_type':type(exc).__name__})
        self.data['phase']='failed' if self.failed else 'completed'
        self.data['ledger_complete']=not any(e['code'] in ('MEMBER_NOT_STARTED','MEMBER_VERIFICATION_FAILED','ALIGNMENT_FAILED') for e in self.data['errors'])
        self.data['finished_perf_counter_ns']=str(time.perf_counter_ns())
        self.save()
        self.finished=True

    def public(self):
        return dict(self.data,directory=str(self.directory))
