import libtorrent as lt
import time
import os
import subprocess
import glob
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_torrent(torrent_link: str, save_path: str) -> str:
    """
    دانلود تورنت (لینک مگنت یا فایل .torrent).
    """
    try:
        ses = lt.session()
        ses.listen_on(6881, 6891)
        settings = {
            'connections_limit': 150,
            'active_downloads': 2,
            'download_rate_limit': 0,
            'upload_rate_limit': 0,
        }
        ses.apply_settings(settings)

        if torrent_link.startswith('magnet:'):
            params = {'save_path': save_path}
            handle = lt.add_magnet_uri(ses, torrent_link, params)
            logger.info("لینک مگنت شناسایی شد. شروع دانلود...")
        else:
            subprocess.run(['wget', torrent_link, '-O', 'temp.torrent'], check=True)
            info = lt.torrent_info('temp.torrent')
            params = {'ti': info, 'save_path': save_path}
            handle = ses.add_torrent(params)
            logger.info("فایل تورنت دانلود شد. شروع دانلود...")

        while not handle.is_seed():
            s = handle.status()
            progress = s.progress * 100
            down_speed = s.download_rate / 1000
            up_speed = s.upload_rate / 1000
            logger.info(f"پیشرفت: {progress:.2f}% | دانلود: {down_speed:.1f} kB/s | آپلود: {up_speed:.1f} kB/s")
            time.sleep(5)

        logger.info("دانلود کامل شد!")
        video_files = glob.glob(os.path.join(save_path, '*.mkv'))
        if not video_files:
            logger.error("هیچ فایل MKV پیدا نشد!")
            return None

        largest_file = max(video_files, key=os.path.getsize)
        logger.info(f"فایل ویدیویی پیدا شد: {largest_file}")
        return largest_file

    except Exception as e:
        logger.error(f"خطا تو دانلود تورنت: {e}")
        return None
    finally:
        if 'ses' in locals():
            ses.pause()

def add_subtitles(video_file: str, subtitle_file: str, encode_type: str = 'hard', 
                 output_encode: str = None, crf: int = 24, 
                 size_string: str = None, remove_sub: bool = True) -> str:
    """
    اضافه کردن زیرنویس به ویدیو با FFmpeg، با استفاده مستقیم از پوشه فونت‌ها.
    """
    try:
        cmd = ['ffmpeg', '-i', video_file]
        if remove_sub:
            cmd.append('-sn')

        # مسیر مستقیم فونت‌ها
        fonts_dir = "/content/torrent-downloader/fonts"
        if not os.path.exists(fonts_dir):
            logger.error(f"پوشه فونت‌ها {fonts_dir} پیدا نشد!")
            return ''

        # تنظیم نوع زیرنویس
        if encode_type == 'hard':
            cmd.extend(['-vf', f"subtitles={subtitle_file}:fontsdir={fonts_dir}"])
        else:
            cmd.extend(['-c:s', 'copy', '-metadata:s:s:0', 'language=eng', subtitle_file])

        # تنظیم کدک ویدیو
        if output_encode == 'x264':
            cmd.extend(['-c:v', 'libx264', '-crf', str(crf), '-preset', 'fast'])
        elif output_encode == 'x265':
            cmd.extend(['-c:v', 'libx265', '-crf', str(crf), '-preset', 'fast'])
        else:
            cmd.extend(['-c:v', 'copy'])

        # تنظیم رزولوشن
        if size_string:
            cmd.extend(['-vf', f'scale={size_string}'])

        cmd.extend(['-c:a', 'copy'])
        return ' '.join(cmd)

    except Exception as e:
        logger.error(f"خطا تو ساخت دستور FFmpeg: {e}")
        return ''

def get_mkv_files(directory: str) -> list:
    """
    پیدا کردن فایل‌های MKV تو پوشه.
    """
    try:
        return glob.glob(os.path.join(directory, '*.mkv'))
    except Exception as e:
        logger.error(f"خطا تو پیدا کردن فایل‌های MKV: {e}")
        return []