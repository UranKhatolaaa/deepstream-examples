#!/bin/bash
###############################################################################
#
# Copyright (c) 2020 NVIDIA CORPORATION.  All Rights Reserved.
#
# NVIDIA CORPORATION and its licensors retain all intellectual property
# and proprietary rights in and to this software, related documentation
# and any modifications thereto.  Any use, reproduction, disclosure or
# distribution of this software and related documentation without an express
# license agreement from NVIDIA CORPORATION is strictly prohibited.
#
###############################################################################

OUT_FILE="streams/classification_test_video.mp4"

IMAGE_URLS=(
"http://farm4.static.flickr.com/3148/2890279040_62501db54b.jpg"
"http://farm4.static.flickr.com/3148/2890279040_62501db54b.jpg"
"http://farm2.static.flickr.com/1261/543851098_625ef13f54.jpg"
"http://farm1.static.flickr.com/61/177891798_7272d7a1b1.jpg"
"https://live.staticflickr.com/3668/9275702496_05b36d4dc7_c_d.jpg"
)


WORK_DIR="/tmp/imagenet-video"
rm -rf "${WORK_DIR}"
CNT=1

if ! which ffmpeg >/dev/null 2>&1 ; then
    "FFmpeg not found. Need to install ffmpeg first."
    exit 1
fi

mkdir -p "${WORK_DIR}"
for IMAGE_URL in ${IMAGE_URLS[@]} ; do
    FILE_NAME="${CNT}.jpg"
    echo "Downloading image ${IMAGE_URL}"
    wget -O "${WORK_DIR}/${CNT}.jpg" "${IMAGE_URL}" -q
    CNT=$((CNT + 1))
    COPY_CNT=0
    while [[ $COPY_CNT -lt 59 ]]; do
        (cd ${WORK_DIR} && ln -sf "${FILE_NAME}" "${CNT}.jpg" )
        CNT=$((CNT + 1))
        COPY_CNT=$((COPY_CNT + 1))
    done
done

echo "Creating video from downloaded images..."
if ffmpeg -r 30 -i "${WORK_DIR}/%d.jpg" \
    -vf "pad=ceil(iw/2)*2:ceil(ih/2)*2" -s 1280x720 -vcodec libx264 \
    -crf 1 -pix_fmt yuv420p "$OUT_FILE" -loglevel 0; then
    echo "Video created at ${OUT_FILE}"
else
    echo "Video creation failed."
fi

rm -rf "${WORK_DIR}"
