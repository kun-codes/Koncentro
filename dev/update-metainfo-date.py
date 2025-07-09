# workaround for updating date in metainfo.xml for linux releases as tbump doesn't support updating dates
import os
import re
from datetime import date

script_dir = os.path.dirname(os.path.abspath(__file__))
xml_path = os.path.join(script_dir, "../installer-scripts/linux/common/com.bishwasaha.Koncentro.metainfo.xml")
xml_path = os.path.normpath(xml_path)

with open(xml_path, "r", encoding="utf-8") as f:
    content = f.read()

today = date.today().isoformat()

new_content = re.sub(r'(date=")[0-9]{4}-[0-9]{2}-[0-9]{2}(")', rf"\g<1>{today}\g<2>", content)

with open(xml_path, "w", encoding="utf-8") as f:
    f.write(new_content)
