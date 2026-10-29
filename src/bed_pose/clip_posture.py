"""CLIP image evidence, with cached text and reproducible experimental decisions.

No bed coordinates, goals, sensors, silhouette overlays or ground truth inputs.
Relative softmax scores are not calibrated posture probabilities.
"""
import base64
from copy import deepcopy
from importlib.metadata import version, PackageNotFoundError
from io import BytesIO
import math
from pathlib import Path

import numpy as np

from .body_state import VERSION
from .clip_assets import MODEL_ID, read_assets,validate_manifest

PROVIDER = 'clip-posture-0.1'
STATE_NAMES = ('lying', 'sitting', 'standing', 'other')
DIRECTION_NAMES = ('supine', 'side', 'prone')
PROMPTS = {
    'lying':['a photo of a person lying down.', 'a photo of a person resting in a lying position.'],
    'sitting':['a photo of a person sitting upright.', 'a photo of a seated person.'],
    'standing':['a photo of a person standing upright.', 'a photo of a person standing on their feet.'],
    'other':['a photo of a person kneeling.', 'a photo of a person crouching.', 'a photo of a person bending over.'],
    'supine':['a photo of a person lying on their back, face up.', 'a photo of a person resting on their back.'],
    'side':['a photo of a person lying on their side.', 'a photo of a person resting on the side of their body.'],
    'prone':['a photo of a person lying on their stomach, face down.', 'a photo of a person resting on their stomach.'],
}


def policy(state_min=.5, direction_min=.5, device='cpu'):
    if (any(type(v) not in (int, float) or not math.isfinite(v) or not 0<=v<=1 for v in (state_min,direction_min))
            or device not in ('cpu','cuda')):raise ValueError('CLIP 점수 기준 또는 실행 장치를 확인하세요.')
    return {'version':PROVIDER, 'state_min':float(state_min), 'direction_min':float(direction_min),
            'prompts':deepcopy(PROMPTS), 'score_policy':'group_softmax_uncalibrated_no_runner_up_margin',
            'text_pooling':'mean_normalized_prompt_embeddings_then_normalize', 'device':device,
            'dtype':'float32', 'threshold_validation':'unvalidated_initial_values', 'tie_tolerance':1e-8,
            'preprocess':'selected_joint_crop_10pct_then_aspect_preserving_square_pad_224_clip_mean_v1'}


def validate_policy(value):
    if not isinstance(value,dict):raise ValueError('Invalid CLIP decision policy')
    base = policy(value.get('state_min'), value.get('direction_min'), value.get('device'))
    if set(value) != set(base)|{'assets_manifest','runtime_versions'}:
        raise ValueError('Invalid CLIP policy fields')
    if any(value[k]!=v for k,v in base.items()):raise ValueError('Unsupported CLIP policy')
    if not isinstance(value['assets_manifest'],dict) or not isinstance(value['runtime_versions'],dict):
        raise ValueError('Missing CLIP provenance')
    validate_manifest(value['assets_manifest'])
    if (set(value['runtime_versions'])!={'torch','transformers','Pillow'}
            or any(v is not None and (not isinstance(v,str) or not v) for v in value['runtime_versions'].values())):
        raise ValueError('Invalid CLIP runtime versions')


def decide(cosines, logit_scale, configuration):
    validate_policy(configuration)
    names = STATE_NAMES+DIRECTION_NAMES
    if (not isinstance(cosines,dict) or set(cosines)!=set(names)
            or any(type(v) not in (int,float) or not math.isfinite(v) or not -1.00001<=v<=1.00001 for v in cosines.values())
            or type(logit_scale) not in (int,float) or not math.isfinite(logit_scale) or logit_scale<=0):
        raise ValueError('Invalid CLIP similarities')
    def group(labels, threshold):
        logits=[cosines[k]*logit_scale for k in labels]
        if not all(math.isfinite(x) for x in logits):raise ValueError('Invalid CLIP logits')
        exps=[math.exp(x-max(logits)) for x in logits];total=sum(exps)
        scores=dict(zip(labels,[x/total for x in exps]));best=max(scores,key=scores.get)
        tied=sum(abs(v-scores[best])<=configuration['tie_tolerance'] for v in scores.values())>1
        return scores, best if not tied and scores[best]>=threshold else None
    states, state = group(STATE_NAMES, configuration['state_min'])
    directions, direction = group(DIRECTION_NAMES, configuration['direction_min'])
    reasons=[]
    if state is None:reasons.append('clip_state_score_insufficient')
    elif state=='lying' and direction is None:reasons.append('clip_direction_score_insufficient')
    return {'state':state or 'unknown', 'lying_direction':direction if state=='lying' and direction else 'unknown',
            'scores':states, 'score_semantics':'uncalibrated_probability',
            'details':{'version':PROVIDER, 'cosine_scores':deepcopy(cosines), 'logit_scale':logit_scale,
                       'direction_scores':directions, 'reasons':reasons}}


def validate_recorded_decision(decision, profile):
    details=decision.get('details') if isinstance(decision,dict) else None
    if not isinstance(details,dict) or set(details)!={'version','cosine_scores','logit_scale','direction_scores','reasons'}:
        raise ValueError('Missing CLIP source scores')
    expected=decide(details['cosine_scores'],details['logit_scale'],profile['decision_policy'])
    if decision!=expected:raise ValueError('CLIP decision differs from recorded scores and policy')


def square_image(rgb):
    from PIL import Image
    if not isinstance(rgb,np.ndarray) or rgb.dtype!=np.uint8 or rgb.ndim!=3 or rgb.shape[2]!=3 or min(rgb.shape[:2])<1:
        raise ValueError('CLIP input must be RGB uint8')
    image=Image.fromarray(rgb);w,h=image.size;scale=224/max(w,h)
    size=(max(1,round(w*scale)),max(1,round(h*scale)))
    resized=image.resize(size,Image.Resampling.BICUBIC)
    result=Image.new('RGB',(224,224),(123,117,104))
    result.paste(resized,((224-size[0])//2,(224-size[1])//2))
    return result


class ClipRuntime:
    """Real Transformers CLIP graph; tiny random graphs can test this boundary."""
    def __init__(self,directory,device):
        import torch
        from transformers import CLIPModel, CLIPProcessor
        if device=='cuda' and not torch.cuda.is_available():raise ValueError('CUDA를 사용할 수 없습니다. CPU를 선택하세요.')
        self.torch=torch;self.device=device
        self.model=CLIPModel.from_pretrained(directory,local_files_only=True,weights_only=True).float().to(device).eval()
        self.processor=CLIPProcessor.from_pretrained(directory,local_files_only=True,use_fast=False)
        texts=[p for name in STATE_NAMES+DIRECTION_NAMES for p in PROMPTS[name]]
        tokens=self.processor.tokenizer(texts,padding=True,return_tensors='pt')
        with torch.inference_mode():
            features=self.model.get_text_features(**{k:v.to(device) for k,v in tokens.items()})
            features=features/features.norm(dim=-1,keepdim=True)
            groups=[];offset=0
            for name in STATE_NAMES+DIRECTION_NAMES:
                length=len(PROMPTS[name]);mean=features[offset:offset+length].mean(dim=0)
                groups.append(mean/mean.norm());offset+=length
            self.text_features=torch.stack(groups)
            self.scale=float(self.model.logit_scale.exp().cpu())

    def similarities(self,image):
        torch=self.torch
        pixels=self.processor.image_processor(images=image,do_resize=False,do_center_crop=False,return_tensors='pt')['pixel_values']
        with torch.inference_mode():
            feature=self.model.get_image_features(pixel_values=pixels.to(self.device))
            feature=feature/feature.norm(dim=-1,keepdim=True)
            values=(feature@self.text_features.T)[0].cpu().tolist()
        return dict(zip(STATE_NAMES+DIRECTION_NAMES,values)),self.scale

    def close(self):
        self.model=self.processor=self.text_features=None


class ClipBodyStateProvider:
    def __init__(self,directory,*,device='cpu',state_min=.5,direction_min=.5):
        self.directory=Path(directory).expanduser().resolve();self.assets=read_assets(self.directory)
        configuration=policy(state_min,direction_min,device)
        versions={}
        for package in ('torch','transformers','Pillow'):
            try:versions[package]=version(package)
            except PackageNotFoundError:versions[package]=None
        configuration.update(assets_manifest=deepcopy(self.assets),runtime_versions=versions)
        self.profile={'version':VERSION,'source':'camera_image', 'model_id':MODEL_ID,
                      'model_sha256':self.assets['files']['pytorch_model.bin'],
                      'preprocess_id':configuration['preprocess'], 'decision_policy':configuration,
                      'execution_kind':'model_inference'}
        self.runtime=None;self.last_input_preview=None

    def open(self):
        if self.runtime is not None:raise ValueError('CLIP provider is already open')
        if read_assets(self.directory,verify=True)!=self.assets:raise ValueError('CLIP 모델 구성이 변경됐습니다.')
        if any(v is None for v in self.profile['decision_policy']['runtime_versions'].values()):
            raise ValueError('CLIP 설치 필요: python -m pip install -e ".[clip]"')
        try:self.runtime=ClipRuntime(self.directory,self.profile['decision_policy']['device'])
        except ImportError as exc:raise ValueError('CLIP 설치 필요: python -m pip install -e ".[clip]"') from exc

    def estimate(self,observation):
        self.last_input_preview=None
        if self.runtime is None:raise ValueError('CLIP provider is not open')
        image=square_image(observation.rgb)
        cosines,scale=self.runtime.similarities(image)
        result=decide(cosines,scale,self.profile['decision_policy'])
        try:
            with BytesIO() as buffer:
                image.save(buffer,format='PNG')
                self.last_input_preview={'stream_frame_id':observation.stream_frame_id,'candidate_id':observation.candidate_id,
                                         'image':'data:image/png;base64,'+base64.b64encode(buffer.getvalue()).decode('ascii')}
        except Exception:
            # A display-only failure must not discard a valid model decision.
            self.last_input_preview=None
        return result

    def close(self):
        if self.runtime is not None:self.runtime.close()
        self.runtime=None;self.last_input_preview=None
