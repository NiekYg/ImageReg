{"nbformat":4,"nbformat_minor":0,"metadata":{"colab":{"provenance":[],"authorship_tag":"ABX9TyNrPpqMGf8dfvUjaH2xco09"},"kernelspec":{"name":"python3","display_name":"Python 3"},"language_info":{"name":"python"}},"cells":[{"cell_type":"code","source":["\n","# -*- coding: utf-8 -*-\n","\"\"\"\n","Created on Thu Jan  2 11:29:06 2020\n","\n","@author: T_ESTIENNE\n","\"\"\"\n","import torch\n","import torch.nn as nn\n","\n","\n","class Identity(nn.Module):\n","    def __init__(self, *args, **kwargs):\n","        super().__init__()\n","\n","    def forward(self, x):\n","        return x\n","\n","\n","def get_activation(activation_type):\n","    activation_type = activation_type.lower()\n","\n","    if activation_type == 'prelu':\n","        return nn.PReLU()\n","    elif activation_type == 'leaky':\n","        return nn.LeakyReLU(inplace=True)\n","    elif activation_type == 'tanh':\n","        return nn.Tanh()\n","    elif activation_type == 'softmax':\n","        return nn.Softmax()\n","    elif activation_type == 'sigmoid':\n","        return nn.Sigmoid()\n","    elif activation_type == 'relu':\n","        return nn.ReLU()\n","    else:\n","        return Identity()\n","\n","class UpPoolingConvolution(nn.Module):\n","\n","    def __init__(self, in_channels, out_channels, activation_type='prelu', \n","                 instance_norm=False, batch_norm=False):\n","        \n","        super(UpPoolingConvolution, self).__init__()\n","        \n","        self.instance_norm = instance_norm or batch_norm\n","        \n","        self.conv = nn.ConvTranspose3d(in_channels, out_channels,\n","                              kernel_size=2,\n","                              padding=0,\n","                              stride=2)\n","\n","        self.activation = get_activation(activation_type)\n","        \n","        if instance_norm:\n","            self.norm = nn.InstanceNorm3d(out_channels)\n","        elif batch_norm:\n","            self.norm = nn.BatchNorm3d(out_channels)\n","            \n","    def forward(self, x):\n","        x = self.conv(x)\n","        if self.instance_norm:\n","            x = self.norm(x)\n","        out = self.activation(x)\n","        return out\n","    \n","class DownPoolingConvolution(nn.Module):\n","\n","    def __init__(self, in_channels, out_channels, activation_type='prelu', \n","                 instance_norm=False, batch_norm=False):\n","        \n","        super(DownPoolingConvolution, self).__init__()\n","        \n","        self.instance_norm = instance_norm or batch_norm\n","        \n","        self.conv = nn.Conv3d(in_channels, out_channels,\n","                              kernel_size=2,\n","                              padding=0,\n","                              stride=2)\n","\n","        self.activation = get_activation(activation_type)\n","        \n","        if instance_norm:\n","            self.norm = nn.InstanceNorm3d(out_channels)\n","        elif batch_norm:\n","            self.norm = nn.BatchNorm3d(out_channels)\n","            \n","    def forward(self, x):\n","        x = self.conv(x)\n","        if self.instance_norm:\n","            x = self.norm(x)\n","        out = self.activation(x)\n","        return out\n","\n","class Convolution(nn.Module):\n","\n","    def __init__(self, in_channels, out_channels, activation_type='prelu',\n","                 instance_norm=False, batch_norm=False):\n","        super(Convolution, self).__init__()\n","        \n","        self.instance_norm = instance_norm or batch_norm\n","\n","        self.conv = nn.Conv3d(in_channels=in_channels,\n","                              out_channels=out_channels,\n","                              kernel_size=3,\n","                              padding=1,\n","                              stride=1)\n"," \n","        self.activation = get_activation(activation_type)\n","        \n","        if instance_norm:\n","            self.norm = nn.InstanceNorm3d(out_channels)\n","        elif batch_norm:\n","            self.norm = nn.BatchNorm3d(out_channels)\n","            \n","    def forward(self, x):\n","        x = self.conv(x)\n","        if self.instance_norm:\n","            x = self.norm(x)\n","        out = self.activation(x)\n","        return out\n","\n","\n","def _make_nConv(in_channels, out_channels, activation, instance_norm,\n","                batch_norm, nb_Conv):\n","    layers = []\n","    layers.append(Convolution(in_channels, out_channels, activation, \n","                              instance_norm, batch_norm))\n","    for _ in range(nb_Conv-1):\n","        layers.append(Convolution(out_channels, out_channels,\n","                                  activation, instance_norm=instance_norm,\n","                                  batch_norm=batch_norm))\n","    \n","    return nn.Sequential(*layers)\n","\n","\n","class ConvBlock(nn.Module):\n","\n","    def __init__(self, in_channels, out_channels,\n","                 activation_type='leaky', instance_norm=False,\n","                 batch_norm=False, nb_Conv=1\n","                 ):\n","\n","        super(ConvBlock, self).__init__()\n","\n","        self.conv_pool = DownPoolingConvolution(in_channels, out_channels, \n","                                                activation_type, \n","                                                instance_norm, batch_norm\n","                                                )\n","\n","        self.nConvs = _make_nConv(out_channels, out_channels, activation_type,\n","                                  instance_norm, batch_norm, nb_Conv)\n","\n","    def forward(self, x):\n","\n","        down = self.conv_pool(x)\n","        out = self.nConvs(down)\n","\n","        return out\n","\n","\n","class DeconvBlock(nn.Module):\n","\n","    def __init__(self, in_channels, out_channels,\n","                 activation_type='leaky',\n","                 instance_norm=False, batch_norm=False, nb_Conv=1\n","                 ):\n","\n","        super(DeconvBlock, self).__init__()\n","\n","\n","        self.conv_tr = UpPoolingConvolution(in_channels, out_channels,\n","                                            activation_type=activation_type,\n","                                            instance_norm=instance_norm,\n","                                            batch_norm=batch_norm)\n","\n","        self.nConvs = _make_nConv(in_channels, out_channels, activation_type,\n","                                  instance_norm, batch_norm, nb_Conv)\n","\n","    def forward(self, x, skip_x=None):\n","        \n","        up = self.conv_tr(x)\n","        cat = torch.cat((up, skip_x), 1)\n","        out = self.nConvs(cat)\n","\n","        out = torch.add(up, out)\n","        return out\n","\n","\n","class InputBlock(nn.Module):\n","\n","    def __init__(self, n_channels, input_channels,\n","                 activation_type='leaky'):\n","\n","        super(InputBlock, self).__init__()\n","\n","        self.add_conv = nn.Conv3d(in_channels=input_channels,\n","                                  out_channels=n_channels,\n","                                  kernel_size=3, padding=1, stride=1)\n","\n","        self.conv = nn.Conv3d(in_channels=n_channels,\n","                              out_channels=n_channels,\n","                              kernel_size=3,\n","                              padding=1,\n","                              stride=1)\n","\n","        self.activation = get_activation(activation_type)\n","\n","    def forward(self, x):\n","\n","        x = self.activation(self.add_conv(x))\n","        out = self.activation(self.conv(x))\n","        out = torch.add(x, out)\n","        \n","        return out\n","\n","\n","\n","class Decoder(nn.Module):\n","\n","    def __init__(self, pool_blocks, channels, out_channels, last_activation,\n","                 activation_type='leaky',\n","                 instance_norm=False, batch_norm=False,\n","                 nb_Convs=[1, 1, 1, 1, 1], freeze_registration=False, \n","                 zeros_init=False, deep_supervision=False):\n","\n","        super(Decoder, self).__init__()\n","\n","        self.conv_list = nn.ModuleList()\n","        self.deep_supervision = deep_supervision\n","                \n","        for i in range(0, pool_blocks):\n","            self.conv_list.append(DeconvBlock(channels[-i-1], channels[-i-2],\n","                                         activation_type, instance_norm, \n","                                         batch_norm, nb_Convs[-i-1]))\n","\n","\n","        self.last_conv = nn.Conv3d(in_channels=channels[-pool_blocks-1],\n","                                   out_channels=out_channels,\n","                                   kernel_size=3,\n","                                   padding=1,\n","                                   stride=1)\n","\n","        self.last_activation = get_activation(last_activation)\n","        \n","        if freeze_registration:\n","            for param in self.last_conv.parameters():\n","                    param.requires_grad = False\n","            \n","        if zeros_init:\n","            torch.nn.init.zeros_(self.last_conv.weight)\n","            torch.nn.init.zeros_(self.last_conv.bias)\n","\n","    def forward(self, skip_x):\n","        \n","        if self.deep_supervision:\n","            pred_list = []\n","            \n","        out = skip_x[-1]\n","           \n","        for i, conv in enumerate(self.conv_list):\n","            if self.deep_supervision:\n","                pred_list.append(out)\n","            out = conv(out, skip_x[-i-2])\n","        \n","        out = self.last_conv(out)\n","        out = self.last_activation(out)\n","\n","        if self.deep_supervision:\n","            pred_list.append(out) # Last one is the final prediction\n","            return pred_list\n","        else:   \n","            return out\n","\n","\n","class Encoder(nn.Module):\n","\n","    def __init__(self, pool_blocks, channels, \n","                 activation_type, input_channel=4,\n","                 instance_norm=False, batch_norm=False,\n","                 nb_Convs=[1, 1, 1, 1, 1]):\n","\n","        super(Encoder, self).__init__()\n","\n","        self.input = InputBlock(channels[0], input_channel,\n","                                activation_type)\n","        self.conv_blocks = nn.ModuleList()\n","\n","        for i in range(pool_blocks):\n","\n","            self.conv_blocks.append(ConvBlock(channels[i], channels[i+1],\n","                                              activation_type, \n","                                              instance_norm, batch_norm,\n","                                              nb_Convs[i]\n","                                              )\n","                                    )\n","\n","    def forward(self, x):\n","        \n","        skip_x = []\n","        skip_x.append(self.input(x))\n","\n","        for conv in self.conv_blocks:\n","            skip_x.append(conv(skip_x[-1]))\n","\n","        return skip_x\n","\n","\n","\n","class DeepSupervisionBlock(nn.Module):\n","        \n","    def __init__(self, pool_blocks, channels, out_channels,\n","                 last_activation):\n","\n","        super(DeepSupervisionBlock, self).__init__()\n","        \n","        self.convs_list = nn.ModuleList()\n","        self.upsample_list = nn.ModuleList()\n","        \n","        for i in range(pool_blocks):\n","            self.convs_list.append(nn.Conv3d(in_channels=channels[-i-1],\n","                                             out_channels=out_channels,\n","                                             kernel_size=3, padding=1, \n","                                             stride=1))\n","            self.upsample_list.append(nn.Upsample(scale_factor=2**(pool_blocks-i)))\n","            \n","        \n","        self.last_activation = get_activation(last_activation)\n","    \n","    def forward(self, x_list):\n","        \n","        pred_list = []\n","\n","        for i, x in enumerate(x_list[:-1]):\n","            \n","            out = self.convs_list[i](x) # Change number of filter\n","            up = self.last_activation(self.upsample_list[i](out)) # Upsample\n","            pred_list.append(up)\n","        \n","        pred_list.append(x_list[-1])\n","        return pred_list\n","             "],"metadata":{"id":"KvL4Mx8s3Q9F"},"execution_count":null,"outputs":[]}]}