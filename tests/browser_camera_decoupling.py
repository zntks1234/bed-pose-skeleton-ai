"""Synthetic camera timing/HTML checks, no physical device or posture accuracy claim."""
import time
import os
import shutil
import numpy as np
from test_web_workspace import WebTests
from bed_pose.latest_camera import LatestCameraSource
from bed_pose.live_engine import LiveEngine
from bed_pose.pose.fake import FakeAdapter
from playwright.sync_api import sync_playwright


def main():
    c=WebTests();c.setUp()
    class Camera:
        index=0
        def open(self):return {'kind':'camera'}
        def read(self):time.sleep(.02);return np.zeros((360,640,3),dtype=np.uint8)
        def close(self):pass
    class Adapter(FakeAdapter):
        def open(self,settings):return dict(super().open(settings),execution_kind='model_inference')
        def estimate(self,model_input):time.sleep(.15);return super().estimate(model_input)
    def factory(source,model,output,options,**kwargs):
        return LiveEngine(LatestCameraSource(Camera()),Adapter(),{'execution_mode':'ordered_sequence'},output)
    c.workspace.factory=factory
    try:
        status,value=c.request('/api/inputs',{'kind':'camera','camera':0,'use_clip':False});assert status==200,value
        sid=value['id']
        with sync_playwright() as p:
            browser=p.chromium.launch(executable_path=os.environ.get('BEDPOSE_CHROMIUM') or shutil.which('chromium'),headless=True,args=['--no-sandbox'])
            page=browser.new_page();errors=[];page.on('pageerror',lambda e:errors.append(str(e)))
            page.goto(c.server.url)
            page.locator('#live-picture').wait_for(state='visible')
            page.wait_for_function("document.getElementById('live-picture').naturalWidth===640")
            assert '관절 오버레이 없음' in page.locator('#live-age').inner_text()
            first=c.workspace.raw_view(sid)['capture_frame_id']
            page.wait_for_function("document.getElementById('live-picture').complete")
            c.wait(lambda x:(x['sessions'][0].get('frame_id') or 0)>1)
            c.wait(lambda _:c.workspace.raw_view(sid)['capture_frame_id']>first)
            page.locator('#live-mode').uncheck();assert page.locator('#live-picture').is_hidden()
            assert not errors,errors
            browser.close()
        print('PASS: camera capture continues during slow inference, independent live image, no stale skeleton overlay, analysis toggle')
    finally:c.cleanup();c.temp.cleanup()

if __name__=='__main__':main()
