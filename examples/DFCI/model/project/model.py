import numpy as np
import random
import torch
import torch.nn as nn


class FCN8s(nn.Module):
    def __init__(self, n_class=3):
        super(FCN8s, self).__init__()
        # conv1
        self.conv1_1 = nn.Conv2d(3, 64, 3, padding=100)
        self.relu1_1 = nn.ReLU(inplace=True)
        self.conv1_2 = nn.Conv2d(64, 64, 3, padding=1)
        self.relu1_2 = nn.ReLU(inplace=True)
        self.pool1 = nn.MaxPool2d(2, stride=2, ceil_mode=True)  # 1/2

        # conv2
        self.conv2_1 = nn.Conv2d(64, 128, 3, padding=1)
        self.relu2_1 = nn.ReLU(inplace=True)
        self.conv2_2 = nn.Conv2d(128, 128, 3, padding=1)
        self.relu2_2 = nn.ReLU(inplace=True)
        self.pool2 = nn.MaxPool2d(2, stride=2, ceil_mode=True)  # 1/4

        # conv3
        self.conv3_1 = nn.Conv2d(128, 256, 3, padding=1)
        self.relu3_1 = nn.ReLU(inplace=True)
        self.conv3_2 = nn.Conv2d(256, 256, 3, padding=1)
        self.relu3_2 = nn.ReLU(inplace=True)
        self.conv3_3 = nn.Conv2d(256, 256, 3, padding=1)
        self.relu3_3 = nn.ReLU(inplace=True)
        self.pool3 = nn.MaxPool2d(2, stride=2, ceil_mode=True)  # 1/8

        # conv4
        self.conv4_1 = nn.Conv2d(256, 512, 3, padding=1)
        self.relu4_1 = nn.ReLU(inplace=True)
        self.conv4_2 = nn.Conv2d(512, 512, 3, padding=1)
        self.relu4_2 = nn.ReLU(inplace=True)
        self.conv4_3 = nn.Conv2d(512, 512, 3, padding=1)
        self.relu4_3 = nn.ReLU(inplace=True)
        self.pool4 = nn.MaxPool2d(2, stride=2, ceil_mode=True)  # 1/16

        # conv5
        self.conv5_1 = nn.Conv2d(512, 512, 3, padding=1)
        self.relu5_1 = nn.ReLU(inplace=True)
        self.conv5_2 = nn.Conv2d(512, 512, 3, padding=1)
        self.relu5_2 = nn.ReLU(inplace=True)
        self.conv5_3 = nn.Conv2d(512, 512, 3, padding=1)
        self.relu5_3 = nn.ReLU(inplace=True)
        self.pool5 = nn.MaxPool2d(2, stride=2, ceil_mode=True)  # 1/32

        # fc6
        self.fc6 = nn.Conv2d(512, 4096, 7)
        self.relu6 = nn.ReLU(inplace=True)
        self.drop6 = nn.Dropout2d()

        # fc7
        self.fc7 = nn.Conv2d(4096, 4096, 1)
        self.relu7 = nn.ReLU(inplace=True)
        self.drop7 = nn.Dropout2d()

        self.score_fr = nn.Conv2d(4096, n_class, 1)
        self.score_pool3 = nn.Conv2d(256, n_class, 1)
        self.score_pool4 = nn.Conv2d(512, n_class, 1)

        self.upscore2 = nn.ConvTranspose2d(n_class, n_class, 4, stride=2, bias=False)
        self.upscore8 = nn.ConvTranspose2d(n_class, n_class, 16, stride=8, bias=False)
        self.upscore_pool4 = nn.ConvTranspose2d(
            n_class, n_class, 4, stride=2, bias=False
        )

        self._initialize_weights()

    def _initialize_weights(self):
        for mod in self.modules():
            if isinstance(mod, nn.Conv2d):
                mod.weight.data.zero_()
                if mod.bias is not None:
                    mod.bias.data.zero_()
            if isinstance(mod, nn.ConvTranspose2d):
                m, k, h, w = mod.weight.data.shape
                if m != k and k != 1:
                    raise RuntimeError(
                        "input + output channels need to be the same or |output| == 1"
                    )
                if h != w:
                    raise RuntimeError("filters need to be square")
                filt = torch.from_numpy(self.upsample_filt(h)).float()
                mod.weight.data[range(m), range(k), :, :] = filt

    def upsample_filt(self, size):
        factor = (size + 1) // 2
        if size % 2 == 1:
            center = factor - 1
        else:
            center = factor - 0.5
        og = np.ogrid[:size, :size]
        return (1 - abs(og[0] - center) / factor) * (1 - abs(og[1] - center) / factor)

    def forward(self, x):
        h = x
        h = self.relu1_1(self.conv1_1(h))
        h = self.relu1_2(self.conv1_2(h))
        h = self.pool1(h)

        h = self.relu2_1(self.conv2_1(h))
        h = self.relu2_2(self.conv2_2(h))
        h = self.pool2(h)

        h = self.relu3_1(self.conv3_1(h))
        h = self.relu3_2(self.conv3_2(h))
        h = self.relu3_3(self.conv3_3(h))
        h = self.pool3(h)
        pool3 = h  # 1/8

        h = self.relu4_1(self.conv4_1(h))
        h = self.relu4_2(self.conv4_2(h))
        h = self.relu4_3(self.conv4_3(h))
        h = self.pool4(h)
        pool4 = h  # 1/16

        h = self.relu5_1(self.conv5_1(h))
        h = self.relu5_2(self.conv5_2(h))
        h = self.relu5_3(self.conv5_3(h))
        h = self.pool5(h)

        h = self.relu6(self.fc6(h))
        h = self.drop6(h)

        h = self.relu7(self.fc7(h))
        h = self.drop7(h)

        h = self.score_fr(h)
        h = self.upscore2(h)
        upscore2 = h  # 1/16

        h = self.score_pool4(pool4)
        h = h[:, :, 5 : 5 + upscore2.size()[2], 5 : 5 + upscore2.size()[3]]
        score_pool4c = h  # 1/16

        h = upscore2 + score_pool4c  # 1/16
        h = self.upscore_pool4(h)
        upscore_pool4 = h  # 1/8

        h = self.score_pool3(pool3)
        h = h[:, :, 9 : 9 + upscore_pool4.size()[2], 9 : 9 + upscore_pool4.size()[3]]
        score_pool3c = h  # 1/8

        h = upscore_pool4 + score_pool3c  # 1/8

        h = self.upscore8(h)
        h = h[:, :, 31 : 31 + x.size()[2], 31 : 31 + x.size()[3]]  # 1/1

        return h


class RSTN(nn.Module):
    def __init__(
        self, crop_margin=20, crop_prob=0.5, crop_sample_batch=1, n_class=3, TEST=None
    ):
        super(RSTN, self).__init__()
        self.TEST = TEST
        self.margin = crop_margin
        self.prob = crop_prob
        self.batch = crop_sample_batch

        # Coarse-scaled Network
        self.coarse_model = FCN8s(n_class)
        # Saliency Transformation Module
        self.saliency1 = nn.Conv2d(n_class, n_class, kernel_size=3, stride=1, padding=1)
        self.relu_saliency1 = nn.ReLU(inplace=True)
        self.saliency2 = nn.Conv2d(n_class, n_class, kernel_size=5, stride=1, padding=2)
        # Fine-scaled Network
        self.fine_model = FCN8s(n_class)

        self._initialize_weights()

    def _initialize_weights(self):
        for name, mod in self.named_children():
            if name == "saliency1":
                nn.init.xavier_normal_(mod.weight.data)
                mod.bias.data.fill_(1)
            elif name == "saliency2":
                mod.weight.data.zero_()
                mod.bias.data = torch.tensor([1.0, 1.5, 2.0])

    def forward(self, image, label=None, mode=None, score=None, mask=None):
        if self.TEST is None:
            assert (
                label is not None
                and mode is not None
                and score is None
                and mask is None
            )
            # Coarse-scaled Network
            h = image
            h = self.coarse_model(h)
            h = torch.sigmoid(h)
            coarse_prob = h
            # Saliency Transformation Module
            h = self.relu_saliency1(self.saliency1(h))
            h = self.saliency2(h)
            saliency = h

            if mode == "S":
                cropped_image, crop_info = self.crop(label, image)
            elif mode == "I":
                cropped_image, crop_info = self.crop(label, image * saliency)
            elif mode == "J":
                cropped_image, crop_info = self.crop(
                    coarse_prob, image * saliency, label
                )
            else:
                raise ValueError("wrong value of mode, should be in ['S', 'I', 'J']")

            # Fine-scaled Network
            h = cropped_image
            h = self.fine_model(h)
            h = self.uncrop(crop_info, h, image)
            h = torch.sigmoid(h)
            fine_prob = h
            return coarse_prob, fine_prob

        elif self.TEST == "C":  # Coarse testing
            assert label is None and mode is None and score is None and mask is None
            # Coarse-scaled Network
            h = image
            h = self.coarse_model(h)
            h = torch.sigmoid(h)
            coarse_prob = h
            return coarse_prob

        elif self.TEST == "O":  # Oracle testing
            assert label is not None and mode is None and score is None and mask is None
            # Coarse-scaled Network
            h = image
            h = self.coarse_model(h)
            h = torch.sigmoid(h)
            # Saliency Transformation Module
            h = self.relu_saliency1(self.saliency1(h))
            h = self.saliency2(h)
            saliency = h
            cropped_image, crop_info = self.crop(label, image * saliency)
            # Fine-scaled Network
            h = cropped_image
            h = self.fine_model(h)
            h = self.uncrop(crop_info, h, image)
            h = torch.sigmoid(h)
            fine_prob = h
            return fine_prob

        elif self.TEST == "F":  # Fine testing
            assert (
                label is None
                and mode is None
                and score is not None
                and mask is not None
            )
            # Saliency Transformation Module
            h = score
            h = self.relu_saliency1(self.saliency1(h))
            h = self.saliency2(h)
            saliency = h
            cropped_image, crop_info = self.crop(mask, image * saliency)
            # Fine-scaled Network
            h = cropped_image
            h = self.fine_model(h)
            h = self.uncrop(crop_info, h, image)
            h = torch.sigmoid(h)
            fine_prob = h
            return fine_prob

        else:
            raise ValueError("wrong value of TEST, should be in [None, 'C', 'F', 'O']")

    def crop(self, prob_map, saliency_data, label=None):
        (N, C, W, H) = prob_map.shape

        binary_mask = prob_map >= 0.5  # torch.uint8
        if label is not None and binary_mask.sum().item() == 0:
            binary_mask = label >= 0.5

        if self.TEST is not None:
            self.left = self.margin
            self.right = self.margin
            self.top = self.margin
            self.bottom = self.margin
        else:
            self.update_margin()

        if binary_mask.sum().item() == 0:  # avoid this by pre-condition in TEST 'F'
            minA = 0
            maxA = W
            minB = 0
            maxB = H
            self.no_forward = True
        else:
            if N > 1:
                mask = torch.zeros(size=(N, C, W, H))
                for n in range(N):
                    cur_mask = binary_mask[n, :, :, :]
                    arr = torch.nonzero(cur_mask)
                    minA = arr[:, 1].min().item()
                    maxA = arr[:, 1].max().item()
                    minB = arr[:, 2].min().item()
                    maxB = arr[:, 2].max().item()
                    bbox = [
                        int(max(minA - self.left, 0)),
                        int(min(maxA + self.right + 1, W)),
                        int(max(minB - self.top, 0)),
                        int(min(maxB + self.bottom + 1, H)),
                    ]
                    mask[n, :, bbox[0] : bbox[1], bbox[2] : bbox[3]] = 1
                saliency_data = saliency_data * mask.cuda()

            arr = torch.nonzero(binary_mask)
            minA = arr[:, 2].min().item()
            maxA = arr[:, 2].max().item()
            minB = arr[:, 3].min().item()
            maxB = arr[:, 3].max().item()
            self.no_forward = False

        bbox = [
            int(max(minA - self.left, 0)),
            int(min(maxA + self.right + 1, W)),
            int(max(minB - self.top, 0)),
            int(min(maxB + self.bottom + 1, H)),
        ]
        cropped_image = saliency_data[:, :, bbox[0] : bbox[1], bbox[2] : bbox[3]]

        if self.no_forward == True and self.TEST == "F":
            cropped_image = torch.zeros_like(cropped_image).cuda()

        crop_info = np.zeros((1, 4), dtype=np.int16)
        crop_info[0] = bbox
        crop_info = torch.from_numpy(crop_info).cuda()

        return cropped_image, crop_info

    def update_margin(self):
        MAX_INT = 256
        if random.randint(0, MAX_INT - 1) >= MAX_INT * self.prob:
            self.left = self.margin
            self.right = self.margin
            self.top = self.margin
            self.bottom = self.margin
        else:
            a = np.zeros(self.batch * 4, dtype=np.uint8)
            for i in range(self.batch * 4):
                a[i] = random.randint(0, self.margin * 2)
            self.left = int(a[0 : self.batch].sum() / self.batch)
            self.right = int(a[self.batch : self.batch * 2].sum() / self.batch)
            self.top = int(a[self.batch * 2 : self.batch * 3].sum() / self.batch)
            self.bottom = int(a[self.batch * 3 : self.batch * 4].sum() / self.batch)

    def uncrop(self, crop_info, cropped_image, image):
        uncropped_image = torch.ones_like(image).cuda()
        uncropped_image *= -9999999
        bbox = crop_info[0]
        uncropped_image[
            :, :, bbox[0].item() : bbox[1].item(), bbox[2].item() : bbox[3].item()
        ] = cropped_image
        return uncropped_image
