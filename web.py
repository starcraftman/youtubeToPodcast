"""
Sanic webserver to serve the podcasts on demand.
"""
import os
import pathlib

import sanic
import sanic.response

import vid

app = sanic.Sanic()
app.config.RESPONSE_TIMEOUT = 600  # Downloading takes long
MAX_CACHE = 2 * 1024 ** 3  # Total video cache, prunes oldest


@app.route("/rss/<series>.rss")
async def get_rss(_, series):
    return await sanic.response.file('web/rss/{}.rss'.format(series))


def remove_old_vids(fnames):
    fnames = list(reversed(sorted(fnames, key=lambda fname: os.stat(fname).st_atime)))
    total_bytes = 0
    for fname in fnames:
        total_bytes += os.stat(fname).st_size

    while total_bytes > MAX_CACHE:
        total_bytes -= os.stat(fnames[0]).st_size
        os.remove(fnames[0])
        del fnames[0]


@app.route("/video/<series>/<episode>.mp4")
async def get_video(_, series, episode):
    episode = int(episode) - 1
    media = pathlib.Path("web/media")

    info_files = media.glob("{}/*.info.json".format(series))
    info_file = sorted(info_files)[episode]
    info = vid.read_json_info(info_file)
    vid.fetch_video(info["webpage_url"], info["format_id"])

    remove_old_vids(list(media.glob('*.mp4')))

    vids = list(media.glob('{}.mp4'.format(info['id'])))
    return await sanic.response.file_stream(vids[0])


def main():
    app.run(host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
