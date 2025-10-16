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

%%writefile /content/torrent-downloader/torrent_downloader.py
import libtorrent as lt
import time
import os
import subprocess
import glob
import logging
import re  # برای استخراج فونت‌ها از .ass

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# فانکشن‌های قبلی (download_torrent و get_mkv_files) رو کپی کن از نسخه قبلی

%%writefile /content/torrent-downloader/torrent_downloader.py
import libtorrent as lt
import time
import os
import subprocess
import glob
import logging
import re

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def download_torrent(torrent_link: str, save_path: str) -> str:
    # کد قبلی رو کپی کن
    pass

def get_mkv_files(directory: str) -> list:
    # کد قبلی رو کپی کن
    pass

def add_subtitles(video_file: str, subtitle_file: str, encode_type: str = 'hard', 
                 output_encode: str = None, crf: int = 24, 
                 size_string: str = None, remove_sub: bool = True) -> str:
    """
    اضافه کردن زیرنویس به ویدیو با FFmpeg، با استفاده فقط از فونت‌های لازم زیرنویس.
    """
    try:
        # استخراج فونت‌های استفاده‌شده از فایل .ass با دیباگ
        with open(subtitle_file, 'r', encoding='utf-8') as f:
            content = f.read()
        styles_section = re.search(r'$$ V4\+ Styles $$(.*?)($$ |$)', content, re.DOTALL)
        needed_fonts = set()
        if styles_section:
            lines = styles_section.group(1).strip().splitlines()
            logger.info(f"خطوط Styles: {lines}")  # دیباگ خطوط
            for line in lines:
                if line.startswith('Style:'):
                    parts = line.split(',')
                    if len(parts) > 2:
                        font_name = parts[1].strip()  # ستون دوم فونت هست
                        needed_fonts.add(font_name)
            logger.info(f"فونت‌های استخراج‌شده: {needed_fonts}")  # دیباگ فونت‌ها
        else:
            logger.warning("بخش [V4+ Styles] پیدا نشد!")

        # پوشه اصلی فونت‌ها
        main_fonts_dir = "/content/torrent-downloader/fonts"

        # ساخت پوشه موقت برای فونت‌های لازم
        temp_fonts_dir = "/content/temp_fonts/"
        os.makedirs(temp_fonts_dir, exist_ok=True)
        # پاک کردن فونت‌های قبلی موقت
        for f in os.listdir(temp_fonts_dir):
            os.remove(os.path.join(temp_fonts_dir, f))

        # کپی فقط فونت‌های لازم به پوشه موقت
        if needed_fonts:
            for font in os.listdir(main_fonts_dir):
                if any(needed.lower() in font.lower() for needed in needed_fonts):
                    os.system(f"cp '{os.path.join(main_fonts_dir, font)}' '{temp_fonts_dir}'")
            logger.info(f"فونت‌های کپی‌شده به موقت: {os.listdir(temp_fonts_dir)}")
        else:
            logger.warning("هیچ فونتی استخراج نشد، همه فونت‌ها کپی می‌شن!")
            for font in os.listdir(main_fonts_dir):
                os.system(f"cp '{os.path.join(main_fonts_dir, font)}' '{temp_fonts_dir}'")

        # چک فونت‌های موقت
        copied_fonts = glob.glob(os.path.join(temp_fonts_dir, "*.*"))
        if not copied_fonts:
            logger.error(f"هیچ فونتی به {temp_fonts_dir} کپی نشد!")
            return ''

        # ساخت دستور FFmpeg
        cmd = ['ffmpeg', '-i', video_file]
        if remove_sub:
            cmd.append('-sn')

        # تنظیم نوع زیرنویس با مسیر فونت موقت
        if encode_type == 'hard':
            cmd.extend(['-vf', f"subtitles={subtitle_file}:fontsdir={temp_fonts_dir}"])
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
        logger.info(f"دستور FFmpeg: {' '.join(cmd)}")
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
