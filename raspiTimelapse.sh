#take single picture
#raspistill -o output.jpg
#take time lapse
raspistill -t 3600000 -tl 60000 -o image%04d.jpg
#sudo apt install libav-tools
#ls *.jpg > stills.txt
#sudo apt install ffmpeg
#ffmpeg -f concat -i stills.txt vid
ffmpeg -r 10 -i image%04d.jpg -r 10 -vcodec libx264 -vf scale=1280:720 timelapse.mp4
