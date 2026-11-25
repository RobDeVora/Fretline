# v1.150: a chord-chart MIDI added before the tab MIDI must end up in the SECOND slot. Usage: /tmp/withsrv.sh python3 test_sheet_order.py CHORDS.mid TAB.mid
import sys
from playwright.sync_api import sync_playwright
ch,tab=sys.argv[1:3]
with sync_playwright() as p:
    b=p.chromium.launch();pg=b.new_page();errs=[];pg.on('pageerror',lambda e:errs.append(str(e)[:200]))
    pg.goto('http://localhost:8769/lab/stems.html');pg.wait_for_timeout(1500)
    pg.set_input_files('#sheetFile',ch);pg.wait_for_function("SHEETFILE",timeout=15000)
    pg.set_input_files('#sheet2File',tab);pg.wait_for_function("SHEETFILE2",timeout=15000);pg.wait_for_timeout(1500)
    r=pg.evaluate("[$('sheetFileName').textContent,$('sheet2FileName').textContent,$('sheetPart').selectedOptions[0].textContent,$('sheet2Part').selectedOptions[0].textContent,$('status').textContent]")
    for x in r:print(x)
    import os;good=r[0].startswith(os.path.basename(tab)) and r[1].startswith(os.path.basename(ch))
    print('PASS' if good and not errs else 'FAIL','(tab in sheet 1, chords in sheet 2)');print('errors',errs);b.close()
