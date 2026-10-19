# Field coding and stereo signalling integration check

This combines Akilan Sivakumar's [#999](https://github.com/Multicorewareinc/x265/pull/999) with Daniel Ramos's [#986](https://github.com/Multicorewareinc/x265/pull/986).
The field restriction was reported during the review of #986; #999 fixes it independently.
No additional encoder source change is proposed here.
Validation prepared with Codex assistance under Daniel's direction.

## Revisions and result

- Upstream master: `0900b28e7057ec0f4492237963aa92b0f6469a76`.
- Frame-packing PR: `f4a24d6c7bdb7f56539f0a6355dd58109cccf3fa`.
- Field fix PR: `cc005e1017d1e8e31bef8e483581fd0ea44fb375`.
- Combined test tree: `853f8390d925547fa4dfd91a4cb52cf828aaa294`.
- Baseline rejection control: #986 without #999.

48 synthetic 8-bit encodes passed: tff/bff, packing 3/4/5, b-adapt 0/1/2, zero and reordered B-frames.
For all 24 comparisons, CLI field splitting and FFmpeg-pre-separated fields produced identical bytes with build-info SEI disabled.
Each 24-frame source produced 48 pictures with 24 top and 24 bottom field indications.
Temporal stereo decoded as L L R R with both input paths.
The independent SEI reader and FFmpeg decoder parsed every stream.
All cases used `--single-sei --no-aud --no-repeat-headers`, exercising the already merged #988 fix.
The baseline rejects ultrafast plus `--field` and produces zero stream bytes.

These are synthetic integration checks with FFmpeg 7.1.5 on Linux x86-64, not the full regression corpus, hardware-display tests or high-bit-depth runs.
Alpha and multiview were compiled in; this matrix does not exercise their output modes.
[Recorded commands, counts and hashes](results.json) retain the original container paths.

## Reproduce

Install the normal x265 build dependencies, FFmpeg with libx264, and Python 3.
From the repository root, build both revisions into the validation directory:

```sh
cmake -S source -B validation/stereo-2026-10-19/build-combined \
  -DCMAKE_BUILD_TYPE=Release -DENABLE_SHARED=OFF -DENABLE_LIBNUMA=OFF \
  -DENABLE_ALPHA=ON -DENABLE_MULTIVIEW=ON
cmake --build validation/stereo-2026-10-19/build-combined -j4
git worktree add --detach validation/stereo-2026-10-19/baseline f4a24d6c7
cmake -S validation/stereo-2026-10-19/baseline/source \
  -B validation/stereo-2026-10-19/build-baseline \
  -DCMAKE_BUILD_TYPE=Release -DENABLE_SHARED=OFF -DENABLE_LIBNUMA=OFF \
  -DENABLE_ALPHA=ON -DENABLE_MULTIVIEW=ON
cmake --build validation/stereo-2026-10-19/build-baseline -j4
python3 validation/stereo-2026-10-19/run.py
```

The script generates its own fixtures, runs the encoders, checks decoder view order and picture count, parses SEI headers independently, and asserts byte equality.
Results and logs go in `output/`.
