# Cameras

Standalone Jetson camera diagnostic. This directory is independent of the motor
firmware and diagnostic menu; `opencv-python` is not needed to run the menu.

## Install

```bash
uv pip install -r cameras/requirements.txt
```

## Run

```bash
uv run python cameras/record.py
uv run python cameras/record.py --duration 5
```

Behavior:

- Runs `v4l2-ctl --list-devices` and matches `exploreHD USB Camera`.
- Picks the first video node listed for each matching camera; expects four.
- If `v4l2-ctl` is unavailable or fails, scans `/dev/video*` and checks capture
  capability when available.
- Sorts by video device number, which is not a stable physical camera identity.
- Records roughly five seconds from each camera sequentially with OpenCV.
- Replaces previous contents under `systemscheck_videos/` and writes AVI clips
  under `systemscheck_videos/latest/`, relative to the working directory.

This records cameras only. Live preview, physical camera naming, timestamped
retention, and discovery improvements are future work.
