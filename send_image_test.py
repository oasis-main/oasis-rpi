import cameraElement as cam

cam.load_state()
user, db, storage = cam.initialize_user(cam.access_config["refresh_token"])
cam.send_image(user, storage, "/home/pi/image.jpg")
