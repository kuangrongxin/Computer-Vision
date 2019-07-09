from keras.layers import Conv2D, UpSampling2D, BatchNormalization, Input, Add, MaxPool2D, Activation, Concatenate
from keras.models import Model
import random

random.seed(123)
nFeatures = 256
nStack = 2
nModules = 3

def  branch_1(inp):
    
    node = BatchNormalization()(inp)
    node = Activation(activation='relu')(node)
    node = Conv2D(32, (1, 1), padding='same')(node)   
    
    return node


def branch_2(inp):
    
    node = BatchNormalization()(inp)
    node = Activation(activation='relu')(node)
    node = Conv2D(32, (1, 1), padding='same')(node)   

    node = BatchNormalization()(node)
    node = Activation(activation='relu')(node)
    node = Conv2D(32, (3, 3), padding='same')(node)

    return node


def branch_3(inp):
    
    node = BatchNormalization()(inp)
    node = Activation(activation='relu')(node)
    node = Conv2D(32, (1, 1), padding='same')(node)   

    node = BatchNormalization()(node)
    node = Activation(activation='relu')(node)
    node = Conv2D(32, (3, 3), padding='same')(node)

    node = BatchNormalization()(node)
    node = Activation(activation='relu')(node)
    node = Conv2D(32, (3, 3), padding='same')(node)
    
    return node


def skipLayer(inp,numOut):
    numIn=inp.shape[3]
    if numIn==numOut:
        return inp
    else:
        return Conv2D(numOut,(1,1),padding='same')(inp)
    

def Inception_Resnet(inp,numOut):
    
    skip=skipLayer(inp,numOut)
    
    branch1=branch_1(inp)
    
    branch2=branch_2(inp)
    
    branch3=branch_3(inp)
    
    concat_=Concatenate()([branch1,branch2,branch3])
    conv_block=Conv2D(numOut, (1, 1), padding='same')(concat_)
    conv_block = BatchNormalization()(conv_block)
    
    return Add()([conv_block, skip])
    

def hourglass(n, f, inp):

    # Upper branch
    up_branch1 = inp

    for i in range(nModules):
        up_branch1=Inception_Resnet(up_branch1,f)

    # Lower branch
    low_branch1 = MaxPool2D((2, 2), strides=2)(inp)

    for i in range(nModules):
        low_branch1 = Inception_Resnet(low_branch1,f)
        
    low_branch2 = None

    if n > 1:
        low_branch2 = hourglass(n - 1, f, low_branch1)
    else:
        low_branch2 = low_branch1
        for i in range(nModules): low_branch2 = Inception_Resnet(low_branch2,f)

    low_branch3 = low_branch2

    for i in range(nModules):
        low_branch3 = Inception_Resnet(low_branch3,f)

    up_branch2 = UpSampling2D(size=(2, 2))(low_branch3)

    # Bring two branches together
    return Add()([up_branch1, up_branch2])



def lin(inp, numOut):

    layer = Conv2D(numOut, (1,1), padding='same')(inp)
    layer = BatchNormalization()(layer)
    layer = Activation(activation='relu')(layer)
    
    return layer


def hg_train(njoints):
    global nOutChannels
    nOutChannels=njoints
    input_ = Input(shape = (None, None, 3))
    conv1=Conv2D(64, (7,7),strides=(2,2), padding='same')(input_)
    conv2=Conv2D(128, (3,3),strides=(1,1), padding='same')(conv1)
    pool=MaxPool2D((2,2),strides=2)(conv2)
    
    conv3=Conv2D(nFeatures, (3,3),strides=(1,1), padding='same')(pool)
    out = []
    inter = conv3

    for i in range(nStack):
        hg = hourglass(4, nFeatures, inter)
        
        # Residual layers at output resolution
        ll = hg
        for j in range(nModules):
            ll = Inception_Resnet(ll,nFeatures)

        ll = lin(ll, nFeatures)
        tmpOut = Conv2D(nOutChannels, (1,1), padding='same', name='stack_%d'%(i))(ll)
        out.append(tmpOut)
        
        if i < nStack:
            ll_ = Conv2D(nFeatures, (1, 1), padding='same')(ll)
            tmpOut_ = Conv2D(nFeatures, (1, 1), padding='same')(tmpOut)
            inter = Add()([inter, ll_, tmpOut_])
            
    model = Model(inputs=input_, outputs=out[-1])

    return model





