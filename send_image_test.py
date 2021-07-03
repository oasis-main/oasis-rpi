import cameraElement as cam

#set proper path for modules
sys.path.append("home/pi/.local/lib/python3.9/site-packages")

cam.load_state()
user, db, storage = cam.initialize_user(cam.access_config["refresh_token"])
cam.send_image(user, storage, "/home/pi/image.jpg")
