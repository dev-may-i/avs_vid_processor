import sys
import subprocess
import argparse
import json

import vp.conf

### Global ############################################################################################################

info = { "file": "", "t_file": "", "out_file": "", "aud_in": "", "aud_ac_in": "", "aud_out": "", "mod": False, "width": "0", "height": "0", "vc": vc, "ac": ac, "crf": crf, "fnum": 0, "fden": 0, "mux": muxer }

#######################################################################################################################
parser = argparse.ArgumentParser()

parser.add_argument("-r", "--res",     type=str, help="Overwrite resolution: [width]x[height] (e.g. 1920x1080)")
parser.add_argument("-c", "--crf",     type=str, help="Overwrite the Constant-Rate-Factor (default crf=25)")
parser.add_argument("-C", "--codec",   type=str, help="Switch Video codec from default. Use [avc] or [hevc]")
parser.add_argument("-a", "--audio",   type=str, help="Switch AAC Audio codec from default. Use [qaac] [ffmpeg] or [eac3to]") 
parser.add_argument("-m", "--mux",     type=str, help="Switch muxing application. Use [ffmpeg] or [mp4box]")
parser.add_argument("-o", "--output",  type=str, help="Out-Filename if different from Input.")
parser.add_argument("file", nargs='?', help="File to process")

args = parser.parse_args()

if (args.res ):
  info["mod"] = True
  info["width"]  = (args.res.split("x"))[0]
  info["height"] = (args.res.split("x"))[1]

if (args.audio ):
  info["ac"] = args.audio

if (args.codec ):
  info["vc"] = args.codec
  
if (args.crf ):
  info["crf"] = args.crf

if (args.mux ):
  info["mux"] = args.mux

if (args.output ):
  info["out_file"] = args.output

if (args.file ):
  info["file"] = (args.file).strip("./")
else:
  print("No file specified. Exiting")
  sys.exit(0)
  
#######################################################################################################################

# cmd = "--Output=\"Video;x %Width%\\ny %Height%\\nfps %FrameRate%\""
# This reduced output doesn't work as python does not pass the argument correctly to mediainfo - for unaccountable reasons!
# It works perfectly on CLI but not within python code. So the easiest way was to use JSON

### Get Infos #########################################################################################################

def get_info():
  info["t_file"] = (info[file])[:-4]

  process = subprocess.Popen(cmd_info, stdout=subprocess.PIPE)
  output = process.communicate()
  o = (str(output).replace("\\r\\n", "").replace("\\xc2\\xa9","c"))[3:-8]   # The JSON Decoder doesn't like the Copyright-Sign
  jo = json.loads(o)
  exit_code = process.wait()  

  # print(jo)
  
  if not info["mod"]:
    info["width"]   = jo["media"]["track"][1]["Width"]
    info["height"]  = jo["media"]["track"][1]["Height"]

  frate             = int(float(jo["media"]["track"][1]["FrameRate"]))
  info["aud_ac_in"] = jo["media"]["track"][2]["Format"]

  if (frate == 23):
    info["fnum"] = 24000
    info["fden"] = 1001
  if (frate == 24):
    info["fnum"] = 24000
    info["fden"] = 1000
  if (frate == 25):
    info["fnum"] = 25000
    info["fden"] = 1000
  if (frate == 29):
    info["fnum"] = 30000
    info["fden"] = 1001
  if (frate == 30):
    info["fnum"] = 30000
    info["fden"] = 1000
  if (frate == 50):
    info["fnum"] = 50000
    info["fden"] = 1000
  if (frate == 59):
    info["fnum"] = 60000
    info["fden"] = 1001
 
  print("########################################################################################") 
  print(info)
  print("########################################################################################")

### demux aac if possible #############################################################################################

def demux_audio_ffmpeg()
  info["aud_out"] = info["t_file"] + ".aac"

  print(cmd_demux_ffmpeg)
  process = subprocess.Popen(cmd_demux_ffmpeg, shell=True, stdout=subprocess.PIPE)
  process.communicate()

def demux_audio_eac3to():
  info["aud_out"] = info["t_file"] + ".aac"

  print(cmd_demux_eac3to)
  process = subprocess.Popen(cmd_demux, shell=True, stdout=subprocess.PIPE)
  process.communicate()


def process_audio_qaac():
  info["aud_out"] = "01.mp4"
  lines = []
  with open("avs.template") as avstmpl:
    l = avstmpl.read()
    lines.append(l)
	  
  lines.append("LWLibAvAudioSource(\"" + info["file"] + "\")" )
  lines.append("return(last)" )

  with open("aud.avs", 'w') as audavs:
    audavs.write('\n'.join(str(l) for l in lines))

  print(cmd_pipemod_qaac)
  process = subprocess.Popen(cmd_pipemod_qaac, shell=True, stdout=subprocess.PIPE)
  process.communicate()

def process_audio_ffmpeg():
  info["aud_out"] = "01.mp4"
  print(cmd_ffmpeg_libfdk_aac)
	
  process = subprocess.Popen(cmd_ffmpeg_libfdk_aac, shell=True, stdout=subprocess.PIPE)
  process.communicate()

### re-compress video in HEVC #########################################################################################

def process_hevc():
  lines = []
  dim = info["width"] + "x" + info["height"]
  spd = str(info["fnum"]) + "/" + str(info["fden"])
  o_file = info["t_file"] + ".h265"
  with open("avs.template") as avstmpl:
    l = avstmpl.read()
    lines.append(l)
	
  lines.append("LWLibAvVideoSource(\"" + file + "\")" )
  lines.append("prefetch(4)")
  lines.append("dfttest(Sigma=2,tbsize=1,lsb=true)")
  if mod:
    lines.append("Dither_resize16(" + info["width"] + "," + info["height"] + ")" )
  lines.append("GradFun3(lsb=true, lsb_in=true, thr=0.4)")
  lines.append("Dither_out()")
  lines.append("return(last)" )

  with open("01.avs", 'w') as vidavs:
    vidavs.write('\n'.join(str(l) for l in lines))
  
  print(cmd_x265)
  process = subprocess.Popen(cmd_x265, shell=True, stdout=subprocess.PIPE)
  process.communicate()
 
### re-compress video in AVC ##########################################################################################

def process_avc():
  lines = []
  o_file = info["t_file"] + ".h264"
  with open("avs.template") as avstmpl:
    l = avstmpl.read()
    lines.append(l)

  lines.append("LWLibAvVideoSource(\"" + file + "\")" )
  lines.append("prefetch(4)")
  lines.append("dfttest(Sigma=2,tbsize=1,lsb=true)")
  if mod:
    lines.append("Dither_resize16(" + info["width"] + "," + info["height"] + ")" )
  lines.append("GradFun3(lsb=true, lsb_in=true, thr=0.4)")
  lines.append("DitherPost()")
  lines.append("return(last)" )

  with open("01.avs", 'w') as vidavs:
    vidavs.write('\n'.join(str(l) for l in lines))

  print(cmd_x264)
  process = subprocess.Popen(cmd_x264, shell=True, stdout=subprocess.PIPE)
  process.communicate()


### multiplex #########################################################################################################

def process_mux_ffmpeg():

  if info["out_file"] == "":
    if info["vc"] == "hevc":
      o_file = info["t_file"] + ".h265"
      info["out_file"] = info["t_file"] + " (HEVC).mp4"
    if info["vc"] == "avc":
      o_file = info["t_file"] + ".h264"
      info["out_file"] = info["t_file"] + "_.mp4"

  print(cmd_mux_ffmpeg)
  process = subprocess.Popen(cmd_mux_ffmpeg, shell=True, stdout=subprocess.PIPE)
  process.communicate()


def process_mux_mp4box():
  if info["out_file"] == "":
    if info["vc"] == "hevc":
      o_file = info["t_file"] + ".h265"
      info["out_file"] = info["t_file"] + " (HEVC).mp4"
      v_t = "\"" + o_file + ":fmt=hevc"
    if info["vc"] == "avc":
      o_file = info["t_file"] + ".h264"
      info["out_file"] = info["t_file"] + "_.mp4"
      v_t = "\"" + o_file + ":fmt=avc1"

  num = info["fnum"]/info["fden"]
  fps = "{:.4f}".format(num)
  ### mp4box stuff

  print(cmd_mux_mp4box)
  process = subprocess.Popen(cmd_mux_mp4box, shell=True, stdout=subprocess.PIPE)
  process.communicate()


### main ##############################################################################################################
if __name__ == "__main__":
  get_info()

  if info["aud_ac_in"] == "AAC":
    if info["mux"] == "ffmpeg":
      demux_audio_ffmpeg() 
    if info["mux"] == "eac3to":
      demux_audio_eac3to()
  else:
    if info["ac"] == "ffmpeg":
      process_audio_ffmpeg()
    if info["ac"] == "qaac":
      process_audio_qaac()

  if info["vc"] == "hevc":
    process_hevc()
  if info["vc"] == "avc":   
    process_avc:

  if info["mux"] == "mp4box":
    process_mux_mp4box()
  if info["mux"] == "ffmpeg":
    process_mux_ffmpeg()

