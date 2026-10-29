"""Real Transformers graph/local reload with tiny RANDOM weights, not pretrained accuracy."""
import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import numpy as np

RUNTIME=all(importlib.util.find_spec(x) for x in ('torch','transformers','PIL'))


@unittest.skipUnless(RUNTIME,'Optional CLIP dependencies are not installed')
class ClipRuntimeTests(unittest.TestCase):
    def test_local_graph_text_cached_image_once_and_no_gradients(self):
        import torch
        from transformers import CLIPModel,CLIPConfig,CLIPTextConfig,CLIPVisionConfig,CLIPTokenizer,CLIPImageProcessor,CLIPProcessor
        from transformers.models.clip.tokenization_clip import bytes_to_unicode
        from bed_pose.clip_posture import ClipRuntime,square_image,STATE_NAMES,DIRECTION_NAMES
        import json
        previous=torch.get_num_threads();torch.set_num_threads(1)
        self.addCleanup(lambda:torch.set_num_threads(previous))
        with tempfile.TemporaryDirectory() as d:
            path=Path(d);tokens=list(bytes_to_unicode().values())
            tokens=tokens+[x+'</w>' for x in tokens]+['<|startoftext|>','<|endoftext|>']
            (path/'vocab.json').write_text(json.dumps(dict(zip(tokens,range(len(tokens))))),encoding='utf-8')
            (path/'merges.txt').write_text('#version: 0.2\n',encoding='utf-8')
            tokenizer=CLIPTokenizer(vocab_file=str(path/'vocab.json'),merges_file=str(path/'merges.txt'))
            CLIPProcessor(tokenizer=tokenizer,image_processor=CLIPImageProcessor()).save_pretrained(path)
            config=CLIPConfig(text_config=CLIPTextConfig(vocab_size=len(tokens),hidden_size=16,intermediate_size=32,
                num_hidden_layers=1,num_attention_heads=2,bos_token_id=512,eos_token_id=513).to_dict(),
                vision_config=CLIPVisionConfig(hidden_size=16,intermediate_size=32,num_hidden_layers=1,
                num_attention_heads=2,image_size=224,patch_size=32).to_dict(),projection_dim=8)
            torch.manual_seed(1);CLIPModel(config).save_pretrained(path)
            runtime=ClipRuntime(path,'cpu')
            with (patch.object(runtime.model,'get_text_features',wraps=runtime.model.get_text_features) as text,
                  patch.object(runtime.model,'get_image_features',wraps=runtime.model.get_image_features) as image):
                rgb=np.zeros((96,160,3),np.uint8)
                a,scale=runtime.similarities(square_image(rgb));b,_=runtime.similarities(square_image(rgb))
                self.assertEqual(a,b);self.assertEqual(set(a),set(STATE_NAMES+DIRECTION_NAMES));self.assertGreater(scale,0)
                self.assertEqual(text.call_count,0);self.assertEqual(image.call_count,2)
                self.assertTrue(all(p.grad is None for p in runtime.model.parameters()))
            runtime.close()


if __name__=='__main__':unittest.main()
