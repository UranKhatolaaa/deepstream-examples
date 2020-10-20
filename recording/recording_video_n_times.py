#
# Example of recording videos in chunks
#
# Pipeline Example:
# gst-launch-1.0 nvarguscamerasrc ! nvv4l2h264enc ! h264parse ! splitmuxsink muxer=qtmux location=video%03d.mp4 max-size-bytes=8000000
#