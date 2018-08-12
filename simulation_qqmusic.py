
# coding: utf-8

# # SW Preparation
# ### ADB tool
# * [Download the ADB zip file for Windows](https://dl.google.com/android/repository/platform-tools-latest-windows.zip)
# * Extract the contents of this ZIP file into an easily accessible folder (such as C:\android\platform-tools)
# * Connect your android phone / tablet and open command prompt to test if adb is working, detail commands can refer this [article](https://www.howtogeek.com/125769/how-to-install-and-use-abd-the-android-debug-bridge-utility/) 
# ```
# C:\Users\rowe8002\AppData\Local\Android\Sdk\platform-tools>adb devices
# List of devices attached
# QMKNW17321007584        device
# ```
# * Add adb executable to Windows PATH [HowTo](https://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/)
# 
# ### OCR tool
# * [Download tesseract Windows binary](https://github.com/tesseract-ocr/tesseract/wiki/Downloads)
# * Install it as its installer instructed
# * Open command prompt to verify the install
# ```
# C:\Users\rowe8002>tesseract --version
# tesseract 3.05.02
#  leptonica-1.75.3
#   libgif 5.1.4 : libjpeg 8d (libjpeg-turbo 1.5.3) : libpng 1.6.34 : libtiff 4.0.9 : zlib 1.2.11 : libwebp 0.6.1 : libopenjp2 2.2.0
# ```
# * Add tessract executable to Windows PATH [HowTo](https://www.howtogeek.com/118594/how-to-edit-your-system-path-for-easy-command-line-access/)
# 
# ### Python package
# * We recommand anacond3 for python package
#     * run **conda search \[packagename\]** to find the package and **conda install \[packagename\]** to install it. 
#     * In case the package doesn't in anaconda repository, run **pip search \[packagename\]** to find the package and **pip install \[packagename\]** to install it
# * **PIL / threading / keyboard / os / pyaudio / subprocess / time / wave** are the packages required for this program
# 
# ### Third party music recognition APP
# * QQ music (this program was initally written for QQ music)
# 
# # HW Preparation
# * android phone (or tablet)
# * usb cable for PC and andriod device connection
# 
# # Notes
# * below code is adjust to adapt 1200x1920 screen size tablet, if you use a different screen size android device, you need to update image crop postion & adb input tap postion accordingly.
# * I would recommand to use big screen device like tablet to run the test, as the track title maybe displayed to 3+ lines if using small screen device, which increase the inaccuracy of ocr. 
# 
# *Any question please contact wei.rong@nielsen.com*

# Switch to recognition screen and start the script
# <img src="guide.png">

# In[1]:


#!usr/bin/env python  
#coding=utf-8  

from PIL import Image
from threading import Thread
import getopt, keyboard, os, pyaudio
import subprocess, sys, time, wave


# In[2]:


########functions for wav playing########
def _wp_init(f):
    p = pyaudio.PyAudio()  
    #open stream  
    stream = p.open(format = p.get_format_from_width(f.getsampwidth()),  
                channels = f.getnchannels(),  
                rate = f.getframerate(),  
                output = True)
    return p, stream

def _wp_run(f,c,s):
    data = f.readframes(c)
    while data:
        if keyboard.is_pressed('q'): break
        s.write(data)
        data = f.readframes(c)

def _wp_deInit(s,p,f):
    s.stop_stream()  
    s.close()
    f.close()
    p.terminate()

def wavPlaying(file):
    chunk = 1024
    wavfile = wave.open(file,"rb")  
    p, stream = _wp_init(wavfile)
    _wp_run(wavfile,chunk,stream)
    _wp_deInit(stream,p,wavfile)    

########functions for image crop########
def _im_crop_save(src,des,box):
    img = Image.open(src+".png")
    img2 = img.crop(box)
    img2.save(des+".png")

def _im_add_suffix(src,suffix):
    if os.path.isfile(src+'.png'):
        os.rename(src+'.png',src+'_'+suffix+'.png')
    
def _im_cleanup(name):
    for i in range(3):
        for j in ['png','txt']:
            f = name+'_check0'+str(i+1)+'.'+j
            try:
                os.remove(f)
            except OSError as e:
                #print(e)
                pass

def _im_cleanup_extracted_string(s):
    if s[:4] == '_ 一 ' and s[-4:] == ' 一 _': s = s[4:-4]
    if s[:2] == '一 ' and s[-2:] == ' 一': s = s[2:-2]
    if s[:2] == '— ' and s[-2:] == ' —': s = s[2:-2]
    if s[:1] == '_' and s[-1:] == '_': s = s[1:-1]
    return s.strip()
    
def _im_extract_track_artist(src):
    ret, error, track1, track2, artist = True, [], '', '', ''

    _im_crop_save(src, src+"_matchup_track", (120, 1255, 1080, 1365))
    
    track1 = _ocr_to_string(src+"_matchup_track")
    track1 = _im_cleanup_extracted_string(track1)
    if not len(track1): error.append('SCREEN_MATCHUP_EXTRACT_TRACK_NORMAL_FAIL')

    #try with psm7 as single line 
    track2 = _ocr_to_string(src+"_matchup_track",False,'-l chi_sim+eng -psm 7')
    track2 = _im_cleanup_extracted_string(track2)
    if not len(track2): error.append('SCREEN_MATCHUP_EXTRACT_TRACK_PSM7_FAIL')

    _im_crop_save(src, src+"_matchup_artist", (120, 1365, 1080, 1405))
    artist = _ocr_to_string(src+"_matchup_artist",False,'-l chi_sim+eng -psm 7')
    artist = _im_cleanup_extracted_string(artist)
    if not len(artist): error.append('SCREEN_MATCHUP_EXTRACT_ARTIST_FAIL')

    if error == []: error.append('SCREEN_MATCHUP_EXTRACT_DONE')

    return ret, '|'.join(error), track1, track2, artist

########functions for image ocr########
def _ocr_to_string(img, cleanup=False, plus='-l chi_sim+eng'):
    subprocess.check_output('tesseract '+img+'.png'+' '+img+' '+plus, shell=True)
    text = ''
    with open(img + '.txt', 'r', encoding='UTF-8') as f:
        text = f.read().strip().replace('\n',' ')
    if cleanup:
        os.remove(img + '.txt')
    return text

########functions for android manipulation########
def _am_formatDuration(d):
    mins = d//60;
    secs = d - mins*60
    return "%02dm%02ds"%(mins,secs)

def _am_getDevices():
    cmd = "adb devices"
    out = subprocess.check_output(cmd.split())
    list = out.decode('utf-8').strip().split('\r\n')
    #print(list)
    return list

def _am_init():
    devices = _am_getDevices()
    if len(devices) <= 1 or '\tdevice' not in devices[-1]:
        cmd = "adb kill-server"
        out = subprocess.check_output(cmd.split())
        time.sleep(5)
        cmd = "adb start-server"
        out = subprocess.check_output(cmd.split())
        list = out.decode('utf-8').strip().split('\r\n')
        print(list)
        if 'successfully' not in list[-1]: return False
    return True

def _am_getScreenSize(st):
    print("%s:_am_getScreenSize " % _am_formatDuration(int(time.time()-st)),end='')
    cmd = "adb shell wm size"
    out = subprocess.check_output(cmd.split())
    size = tuple((out.decode('utf-8').strip().split('\r\n')[0].split(' ')[2].split('x')))
    print(size)
    return size

def _am_launchApp(st):
    print("%s:_am_launchApp" % _am_formatDuration(int(time.time()-st)))

def _am_CaptureFullScreen(des):
    cmd = "adb shell screencap -p /sdcard/screencap.png"
    out = subprocess.check_output(cmd.split())
    cmd = "adb pull /sdcard/screencap.png %s%s" % (des,".png")
    out = subprocess.check_output(cmd.split())
    if 'pulled' not in out.decode('utf-8').strip():
        print("%s:screencap or pull failed, exit..." % _am_formatDuration(int(time.time()-st)))
        return False, "SCREENCAP_OR_PULL_FAILED"
    return True, "SCREENCAP_AND_PULL_DONE"

def _am_pressRecognition():
    cmd = "adb shell input tap 300 1715"        #this is recognition icon position
    out = subprocess.check_output(cmd.split())

def _am_pressBack():
    cmd = "adb shell input tap 40 90"           #this is back arrow position
    out = subprocess.check_output(cmd.split())

def _am_onScreenAction(fn,out,ss,pos,rc):
    tsvFile = open(os.path.join(out,fn)+'.tsv','a')
    
    formatPos = _am_formatDuration(pos)
    print("%s\t"%formatPos, end='')
    
    ret, err = True, 'SCREEN_UNKNOWN'

    #caputre the full sceen
    name = os.path.join(out,"%s_%s" % (fn,pos))
    ret, err = _am_CaptureFullScreen(name)
    if not ret: return ret,err

    #crop to have multiple check-point sub-images to identify screen
    _im_crop_save(name, name+"_check01", (0, 180, 1200, 240))   #匹配到以下结果
    _im_crop_save(name, name+"_check02", (0, 610, 1200, 675))   #请求超时/未匹配到结果/无网络连接
    _im_crop_save(name, name+"_check03", (0, 1505, 1200, 1555)) #重试/停止识别/开始识别/重新识别/查看识别历史

    #rc：round count, if first round screen is match_up, skip it as it may be presenting the previous track meta
    if '匹配到以下结果' in _ocr_to_string(name+"_check01") and rc != 0: 
        ret, err, track1, track2, artist = _im_extract_track_artist(name)
        print("%s\t%s\t%s\t%s"%(err,track1,track2,artist),end='')
        tsvFile.write("%s\t%s\t%s\t%s"%(pos,track1,track2,artist))
        _im_add_suffix(name,'matchup')
        _am_pressBack()
        _am_pressRecognition()
    elif '停止识别' in _ocr_to_string(name+"_check03"):
        print("SCREEN_MATCHING",end='')
        tsvFile.write("%s\t\t\t"%pos)
        ret, err =  True, 'SCREEN_MATCHING'
        _im_add_suffix(name,'matching')
    else:
        check02str = _ocr_to_string(name+"_check02")
        if '未匹配到结果' in check02str:
            print("SCREEN_NO_MATCH",end='')
            _im_add_suffix(name,'nomatch')
            ret, err =  True, 'SCREEN_NO_MATCH'
        elif '请求超时' in check02str:
            print("SCREEN_REQ_TIMEOUT",end='')
            _im_add_suffix(name,'timeout')
            ret, err =  True, 'SCREEN_REQ_TIMEOUT'
        elif '发生错误了' in check02str:
            print("SCREEN_ERROR_OCCUR",end='')
            _im_add_suffix(name,'errOccur')
            ret, err =  True, 'SCREEN_ERROR_OCCUR'
        else:
            print("SCREEN_UNKNOWN",end='')
            _im_add_suffix(name,'unkown')
            ret, err = True, 'SCREEN_UNKNOWN'
        tsvFile.write("%s\t\t\t"%pos)
        _am_pressBack()
        _am_pressRecognition
    
    _im_cleanup(name)
    print('\n',end='')
    tsvFile.write('\n')
    tsvFile.close()
    return ret, err

def androidManipulation(t,inF,outD,screenSize,interval):
    roundCount = 0 #in case the match up screen is presenting previous recognized track

    startTime = time.time()
    while t.isAlive():
        pos = int(time.time()-startTime)
        if (pos % interval) == 0:
            ret,errorInfo = _am_onScreenAction(inF,outD,screenSize,pos,roundCount)
            roundCount = roundCount + 1
            if not ret:
                print(errorInfo)
                break

########wav play & android manipulation threads########
def simuThreads(inF,outD,screenSize,interval):
    threadWp = Thread(target=wavPlaying, args=(inF,))
    threadWp.start()

    threadAm = Thread(target=androidManipulation, args=(threadWp,os.path.basename(inF),outD,screenSize,interval,))
    threadAm.start()

    threadWp.join()
    threadAm.join()


# In[3]:


def usage():
    print("Usage:")
    print("python simulation_qqmusic.py --wav_dir=$wavDir --out_dir=$outDir --interval=$interval")
    print("  $wav_dir: the input directory for wave files")
    print("  $out_dir: the output directory for result tsv file and corresponding images")
    print("  $interval: optional, the interval (in second) to check screen content, default is 60 seconds")
    exit()

def main(argv):
    opts, args = getopt.getopt(argv[1:], "h", ['wav_dir=', 'out_dir=', 'interval='])

    wavDir,outDir,interval = '','',60

    for o, a in opts:
        if o in ('-h'):
            usage()
        elif o in ('--wav_dir'):
            wavDir = a
        elif o in ('--out_dir'):
            outDir = a
        elif o in ('--interval'):
            interval = a

    if wavDir == '' or outDir == '':
        print("missing parameter, please check usage.")
        usage()

    try:
        int(interval)
    except ValueError:
        print("invalid interval, please check usage.")
        usage()

    print("wav files directory is : %s"%wavDir)
    print("   output directory is : %s"%outDir)
    print("           interval is : %s seconds"%interval)
    
    if not os.path.isdir(wavDir):
        print("wav directory %s does NOT exist, exit...")
        exit()

    fileList = os.listdir(wavDir)
    wavList = []
    for i in fileList:
        ext = os.path.splitext(os.path.basename(i))[1]
        if '.wav' == ext:
            wavList.append(i)

    if os.path.isdir(outDir): os.rename(outDir,outDir+'_'+time.strftime('%Y%m%d_%H%M%S',time.localtime()))
    os.makedirs(outDir, exist_ok=True)

    #init andriod device
    if not _am_init():
        print("android manipulation exit due to adb init failure...")
        return
    
    #get screen size. TODO: pass screenSize as parameter for tap & crop
    #screenSize = _am_getScreenSize(startTime)
    #_am_launchApp(startTime)
    screenSize = ('1200', '1920')
    
    totalCount = 0
    for i in sorted(wavList):
        totalCount = totalCount + 1
        print("[%03d: %s]"%(totalCount,i))
        simuThreads(os.path.join(wavDir,i),outDir,screenSize,int(interval))


# In[4]:


#sys.argv = ['simulation_qqmusic.py', '--wav_dir', 'wav_folder_test', '--out_dir', '_out_test', '--interval', '45']
#sys.argv = ['simulation_qqmusic.py', '--wav_dir', '_archive\wav_folder_test', '--out_dir', '_out_test']

##########Main()##########
if __name__ == '__main__':
    main(sys.argv)

