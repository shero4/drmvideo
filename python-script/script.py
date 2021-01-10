#imports
import subprocess
import os,binascii
import xml.etree.ElementTree as ET
import json
import os, errno
import shutil
def execute( bash_command ): #for running bash command
        # to remove any output
        # p = subprocess.Popen(bash_command, stdout=subprocess.PIPE) 
        p = subprocess.Popen(bash_command)    
        (output, err) = p.communicate()
        print(err)
        return err

def createdir( path ): #for creating any directory
    try:
        try:
            original_umask = os.umask(0)
            os.makedirs(path, 0o777)
        finally:
            os.umask(original_umask)
    except OSError as e:
        if e.errno != errno.EEXIST:
            raise

bitrates = { "700":288, "1000":360, "1500":480, "2000":576 }
offbitrate = "1000"

path = './video_upload'
files = os.listdir(path)
for name in files:

    #variable names
    x,y = os.path.splitext(name)
    vidName = x
    
    createdir('./video_uploaded/' + vidName)

    #split source file to audio and video
    
    command = ["ffmpeg", "-i", "./video_upload/"+vidName+".mp4" ,"-c:v" ,"copy", "-an", "./video_uploaded/"+vidName+"/"+vidName+"-video.mp4"]
    execute(command)
    command = ["ffmpeg", "-i", "./video_upload/"+vidName+".mp4" ,"-c:a" ,"copy", "-vn", "./video_uploaded/"+vidName+"/"+vidName+"-audio.mp4"]
    execute(command)

    #change to different bitrates

    #scale="trunc(oh*a/2)*2:720"

    for bitrate in bitrates:
        # wierd = '''"scale='trunc(oh*a/2)*2:'''+str(bitrates[bitrate])+"'\""
        wierd = '''scale='trunc(oh*a/2)*2:'''+str(bitrates[bitrate])+"'"
        # wierd = "scale=\"trunc(oh*a/2)*2:360\""
        command = ["ffmpeg", "-i", "./video_uploaded/"+vidName+"/"+vidName+"-video.mp4", "-an", "-c:v" ,"libx264","-preset", "veryslow" ,"-profile:v", "high", "-level", "4.2", "-b:v", bitrate+"k", "-minrate", bitrate+"k", "-maxrate", bitrate+"k", "-bufsize", str(int(bitrate)*2)+"k", "-g", "96", "-keyint_min", "96", "-sc_threshold", "0", "-filter:v", wierd, "-pix_fmt", "yuv420p", "./video_uploaded/"+vidName+"/"+vidName+"-video-"+bitrate+"k.mp4"]
        execute(command)

    #make new keys and add to json

    KID = "0x" + str(binascii.b2a_hex(os.urandom(16)).upper())
    val = "0x" + str(binascii.b2a_hex(os.urandom(16)).upper())

    entry = {
        "value": val, 
        "kid": KID
    }
    with open("./video_uploaded/"+vidName+"/"+vidName+".json", mode='w') as feedsjson:
        json.dump(entry, feedsjson)

    # change keys in crypt.xml

    crypt = ET.parse('crypt.xml')
    elem = crypt.getroot()
    elem[1][0].attrib["KID"] = KID
    elem[1][0].attrib["value"] = val
    crypt.write('crypt.xml')

    #encrypt files using clearkey encryption

    for bitrate in bitrates:
        command = ["MP4Box", "-crypt", "crypt.xml", "./video_uploaded/"+vidName+"/"+vidName+"-video-"+bitrate+"k.mp4", "-out", "./video_uploaded/"+vidName+"/"+vidName+"-video-"+bitrate+"k-encrypted.mp4"]
        execute(command)
    # for audio
    execute(["MP4Box", "-crypt", "crypt.xml", "./video_uploaded/"+vidName+"/"+vidName+"-audio.mp4", "-out", "./video_uploaded/"+vidName+"/"+vidName+"-audio-encrypted.mp4"])

    #create folder
    createdir('./video_online/'+vidName+'/dash')
    createdir('./video_offline/'+vidName+'/dash')

    #online

    command = ["MP4Box", "-dash", "4000", "-rap", "-frag-rap", "-sample-groups-traf", "-profile", "dashavc264:live", "-bs-switching", "multi", "-url-template"]

    for bitrate in bitrates:
        command.append("video_uploaded/"+vidName+"/"+vidName+"-video-"+bitrate+"k-encrypted.mp4")
    command.append("video_uploaded/"+vidName+"/"+vidName+"-audio-encrypted.mp4")
    command.append("-out")
    command.append("video_online/"+vidName+"/dash/manifest.mp4")
    execute(command)

    #offline

    command = ["MP4Box", "-dash","4000", "-rap", "-frag-rap", "-sample-groups-traf", "-profile", "dashavc264:live", "-bs-switching", "no", "-url-template", "./video_uploaded/"+vidName+"/"+vidName+"-video-"+offbitrate+"k-encrypted.mp4#video", "./video_uploaded/"+vidName+"/"+vidName+"-audio-encrypted.mp4#audio", "-out", "video_offline/"+vidName+"/dash/manifest.mp4"]
    execute(command)

    print("Completed " + vidName + " :)") 
    #upload to s3 bucket script



    #shift file to video_uploaded folder
    shutil.move("./video_upload/" + vidName + ".mp4", "./video_uploaded")

