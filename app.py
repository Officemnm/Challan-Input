from flask import Flask, request, jsonify, render_template_string
import requests
import re
import time
from datetime import datetime, timedelta, timezone
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CONFIGURATION ---
app = Flask(__name__)

# --- MNM SOFTWARE DESIGN (Updated Colors & Order) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <title>Sewing Input Portal</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@500;700&display=swap" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    
    <style>
        :root {
            --bg-body: #0a0a0f;
            --bg-card: #16161f;
            --text-primary: #FFFFFF;
            --text-secondary: #8b8b9e;
            
            /* --- COLOR PALETTE --- */
            --col-orange: #FF7A00;
            --col-blue: #06b6d4;
            --col-purple: #8B5CF6;
            --col-green: #10B981;
            
            --border-color: rgba(255, 255, 255, 0.08);
            --gradient-card: linear-gradient(145deg, rgba(22, 22, 31, 0.9) 0%, rgba(16, 16, 22, 0.95) 100%);
            --transition-smooth: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        }
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: 'Inter', sans-serif; }
        body {
            background: var(--bg-body); color: var(--text-primary); min-height: 100vh;
            display: flex; justify-content: center; align-items: center; overflow-x: hidden; position: relative;
        }
        .bg-orb {
            position: fixed; border-radius: 50%; filter: blur(80px); opacity: 0.4;
            animation: orbFloat 20s ease-in-out infinite; pointer-events: none; z-index: 0;
        }
        .orb-1 { width: 300px; height: 300px; background: var(--col-orange); top: -100px; left: -100px; }
        .orb-2 { width: 250px; height: 250px; background: var(--col-purple); bottom: -50px; right: -50px; animation-delay: -5s; }
        .orb-3 { width: 150px; height: 150px; background: var(--col-green); top: 50%; left: 50%; transform: translate(-50%, -50%); animation-delay: -10s; }
        @keyframes orbFloat {
            0%, 100% { transform: translate(0, 0) scale(1); }
            50% { transform: translate(-20px, 20px) scale(0.95); }
        }
        .main-container { position: relative; z-index: 10; width: 100%; max-width: 440px; padding: 20px; }
        .glass-card {
            background: var(--gradient-card); border: 1px solid var(--border-color); border-radius: 24px; padding: 40px 35px;
            backdrop-filter: blur(20px); box-shadow: 0 25px 80px rgba(0, 0, 0, 0.5);
            animation: cardAppear 0.8s cubic-bezier(0.4, 0, 0.2, 1); position: relative; overflow: hidden;
        }
        @keyframes cardAppear { from { opacity: 0; transform: translateY(30px) scale(0.95); } to { opacity: 1; transform: translateY(0) scale(1); } }
        .brand-section { text-align: center; margin-bottom: 30px; }
        .brand-icon {
            width: 60px; height: 60px; background: linear-gradient(135deg, #FF7A00 0%, #FF9A40 100%); border-radius: 16px;
            display: inline-flex; align-items: center; justify-content: center; font-size: 28px; color: white;
            margin-bottom: 15px; box-shadow: 0 10px 30px rgba(255, 122, 0, 0.3);
        }
        .brand-title { font-size: 24px; font-weight: 900; letter-spacing: -0.5px; }
        .brand-title span { color: var(--col-orange); }
        
        .form-control-custom {
            width: 100%; padding: 18px; background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color);
            border-radius: 16px; color: white; font-size: 16px; font-weight: 700; text-align: center; letter-spacing: 2px;
            outline: none; transition: var(--transition-smooth); margin-bottom: 25px;
        }
        .form-control-custom:focus { border-color: var(--col-orange); background: rgba(255, 122, 0, 0.05); box-shadow: 0 0 0 4px rgba(255, 122, 0, 0.2); }
        
        /* --- NEW STYLISH SELECTOR --- */
        .company-grid {
            display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin-bottom: 30px;
        }
        .company-option { position: relative; height: 55px; }
        .company-option input { position: absolute; opacity: 0; cursor: pointer; height: 0; width: 0; }
        
        .company-label {
            display: flex; align-items: center; justify-content: center; width: 100%; height: 100%;
            background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color);
            border-radius: 14px; 
            
            /* Font Change as requested */
            font-family: 'JetBrains Mono', monospace; 
            font-size: 11px; font-weight: 700; text-align: center;
            color: var(--text-secondary); cursor: pointer; transition: all 0.3s ease;
            text-transform: uppercase; letter-spacing: -0.5px;
        }

        /* --- INDIVIDUAL COLORS & SHADOWS --- */
        
        /* 1. Cotton Clothing (Orange) */
        #comp2:checked + .company-label {
            border-color: var(--col-orange);
            background: rgba(255, 122, 0, 0.1);
            color: var(--col-orange);
            box-shadow: 0 0 20px rgba(255, 122, 0, 0.4);
            transform: translateY(-2px);
        }

        /* 2. Cotton Club (Blue) */
        #comp1:checked + .company-label {
            border-color: var(--col-blue);
            background: rgba(6, 182, 212, 0.1);
            color: var(--col-blue);
            box-shadow: 0 0 20px rgba(6, 182, 212, 0.4);
            transform: translateY(-2px);
        }

        /* 3. Cotton Clout (Purple) */
        #comp4:checked + .company-label {
            border-color: var(--col-purple);
            background: rgba(139, 92, 246, 0.1);
            color: var(--col-purple);
            box-shadow: 0 0 20px rgba(139, 92, 246, 0.4);
            transform: translateY(-2px);
        }

        /* 4. Tropical Knitex (Green) */
        #comp3:checked + .company-label {
            border-color: var(--col-green);
            background: rgba(16, 185, 129, 0.1);
            color: var(--col-green);
            box-shadow: 0 0 20px rgba(16, 185, 129, 0.4);
            transform: translateY(-2px);
        }

        /* Hover Effect */
        .company-label:hover { background: rgba(255, 255, 255, 0.06); }


        .btn-action {
            width: 100%; padding: 16px; background: linear-gradient(135deg, #FF7A00 0%, #FF9A40 100%); color: white; border: none; border-radius: 16px;
            font-weight: 700; font-size: 16px; cursor: pointer; transition: var(--transition-smooth); letter-spacing: 1px; text-transform: uppercase;
        }
        .btn-action:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(255, 122, 0, 0.3); }
        
        .result-box { display: none; margin-top: 30px; animation: slideUp 0.5s ease-out; }
        @keyframes slideUp { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        .info-card { background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); border-radius: 16px; padding: 20px; text-align: center; margin-bottom: 20px; }
        .challan-text { font-size: 22px; font-weight: 800; color: white; margin-bottom: 5px; }
        .sys-text { font-size: 13px; color: var(--text-secondary); font-weight: 500; }
        .status-icon-success { font-size: 40px; color: var(--col-green); margin-bottom: 15px; filter: drop-shadow(0 0 10px rgba(16, 185, 129, 0.4)); }
        .btn-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; }
        .btn-outline {
            background: rgba(255, 255, 255, 0.03); border: 1px solid var(--border-color); color: var(--text-secondary);
            padding: 15px; border-radius: 12px; font-size: 13px; text-decoration: none; display: flex; flex-direction: column;
            align-items: center; gap: 8px; transition: var(--transition-smooth); font-weight: 600;
        }
        .btn-outline:hover { background: rgba(255, 255, 255, 0.08); border-color: var(--text-primary); color: white; transform: translateY(-2px); }
        .error-message {
            background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.2); color: #F87171;
            padding: 15px; border-radius: 12px; font-size: 14px; font-weight: 500; display: flex; align-items: center; gap: 10px; justify-content: center; margin-bottom: 15px;
        }
        #loading-overlay {
            display: none; position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(22, 22, 31, 0.9);
            z-index: 100; flex-direction: column; justify-content: center; align-items: center; backdrop-filter: blur(5px); border-radius: 24px;
        }
        .spinner {
            width: 50px; height: 50px; border: 4px solid rgba(255, 122, 0, 0.1); border-top: 4px solid var(--col-orange);
            border-right: 4px solid var(--col-orange); border-radius: 50%; animation: spin 0.8s linear infinite; box-shadow: 0 0 20px rgba(255, 122, 0, 0.4);
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .footer-credit { text-align: center; margin-top: 30px; color: var(--text-secondary); font-size: 11px; opacity: 0.6; font-weight: 500; letter-spacing: 0.5px; }
        .dev-name { color: var(--col-orange); font-weight: 700; text-transform: uppercase; }
    </style>
</head>
<body>
    <div class="bg-orb orb-1"></div><div class="bg-orb orb-2"></div><div class="bg-orb orb-3"></div>
    <div class="main-container">
        <div class="glass-card">
            <div id="loading-overlay">
                <div class="spinner"></div>
                <div style="margin-top: 15px; font-weight: 600; color: var(--col-orange); letter-spacing: 1px;">PROCESSING...</div>
            </div>
            <div class="brand-section">
                <div class="brand-icon"><i class="fa-solid fa-layer-group"></i></div>
                <div class="brand-title">SEWING<span>INPUT</span></div>
                <div class="brand-subtitle">MNM Production System</div>
            </div>
            <form id="mainForm">
                <div class="input-group-custom">
                    <input type="number" inputmode="numeric" id="challanNo" class="form-control-custom" placeholder="ENTER CHALLAN NO" required autocomplete="off">
                </div>

                <div class="company-grid">
                    <div class="company-option">
                        <input type="radio" name="company" id="comp2" value="2" checked>
                        <label for="comp2" class="company-label">Cotton Clothing</label>
                    </div>

                    <div class="company-option">
                        <input type="radio" name="company" id="comp1" value="1">
                        <label for="comp1" class="company-label">Cotton Club BD</label>
                    </div>

                    <div class="company-option">
                        <input type="radio" name="company" id="comp4" value="4">
                        <label for="comp4" class="company-label">Cotton Clout BD</label>
                    </div>

                    <div class="company-option">
                        <input type="radio" name="company" id="comp3" value="3">
                        <label for="comp3" class="company-label">Tropical Knitex</label>
                    </div>
                </div>

                <button type="submit" class="btn-action">Submit Data <i class="fa-solid fa-arrow-right ms-2"></i></button>
            </form>
            <div id="successBox" class="result-box">
                <div style="text-align: center;"><i class="fa-solid fa-circle-check status-icon-success"></i></div>
                <div class="info-card">
                    <div class="challan-text" id="successChallan">---</div>
                    <div class="sys-text" id="sysId">---</div>
                </div>
                <div class="btn-grid">
                    <a href="#" id="link1" target="_blank" class="btn-outline"><i class="fa-solid fa-print"></i> Call List</a>
                    <a href="#" id="link2" target="_blank" class="btn-outline"><i class="fa-solid fa-file-invoice"></i> Challan</a>
                </div>
                <div style="text-align: center; margin-top: 25px;">
                    <a href="#" onclick="resetUI()" style="color: var(--text-secondary); text-decoration: none; font-size: 13px; font-weight: 500;"><i class="fa-solid fa-rotate-right me-1"></i> Input Another</a>
                </div>
            </div>
            <div id="errorBox" class="result-box">
                <div class="error-message"><i class="fa-solid fa-triangle-exclamation"></i> <span id="errorMsg">Unknown Error</span></div>
                <button onclick="resetUI()" class="btn-outline w-100" style="color: var(--accent-red); border-color: rgba(239, 68, 68, 0.3);">Try Again</button>
            </div>
            <div class="footer-credit">System Developed By <span class="dev-name">Mehedi Hasan</span></div>
        </div>
    </div>
    <script>
        const form = document.getElementById('mainForm');
        const input = document.getElementById('challanNo');
        const loader = document.getElementById('loading-overlay');
        const successBox = document.getElementById('successBox');
        const errorBox = document.getElementById('errorBox');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const val = input.value;
            const companyEl = document.querySelector('input[name="company"]:checked');
            
            if(!val) { alert("Please Enter Challan No"); return; }
            if(!companyEl) { alert("Please Select a Company"); return; }

            const companyId = companyEl.value;
            input.blur(); 
            loader.style.display = 'flex';
            successBox.style.display = 'none';
            errorBox.style.display = 'none';

            try {
                const req = await fetch('/process', {
                    method: 'POST', 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify({ challan: val, company_id: companyId })
                });
                const res = await req.json();
                loader.style.display = 'none';

                if(res.status === 'success') {
                    document.getElementById('successChallan').innerText = res.challan_no;
                    document.getElementById('sysId').innerText = "SYS ID: " + res.system_id;
                    document.getElementById('link1').href = res.report1_url;
                    document.getElementById('link2').href = res.report2_url;
                    successBox.style.display = 'block';
                } else {
                    document.getElementById('errorMsg').innerText = res.message;
                    errorBox.style.display = 'block';
                }
            } catch (err) {
                loader.style.display = 'none';
                document.getElementById('errorMsg').innerText = "Server Connection Error";
                errorBox.style.display = 'block';
            }
        });

        function resetUI() {
            input.value = '';
            successBox.style.display = 'none';
            errorBox.style.display = 'none';
            input.focus();
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---
def process_data(user_input, client_ua, company_id):
    base_url = "http://180.92.235.190:8022/erp"
    
    headers_common = {
        'User-Agent': client_ua if client_ua else 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://180.92.235.190:8022/',
        'Referer': f"{base_url}/login.php"
    }

    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)

    try:
        # 1. Login
        session.post(f"{base_url}/login.php", data={'txt_userid': 'input1.clothing-cutting', 'txt_password': '123456', 'submit': 'Login'}, headers=headers_common)

        # 2. Session Activate
        headers_menu = headers_common.copy()
        headers_menu['Referer'] = f"{base_url}/production/bundle_wise_sewing_input.php?permission=1_1_2_1"
        try:
            session.get(f"{base_url}/tools/valid_user_action.php?menuid=724", headers=headers_menu)
            session.get(f"{base_url}/includes/common_functions_for_js.php?data=724_7_406&action=create_menu_session", headers=headers_menu)
        except: pass

        # 3. Logic Setup (Direct Assignment)
        cbo_logic = str(company_id) 
        
        ctrl_url = f"{base_url}/production/requires/bundle_wise_cutting_delevar_to_input_controller.php"
        headers_ajax = headers_common.copy()
        headers_ajax['X-Requested-With'] = 'XMLHttpRequest'
        if 'Content-Type' in headers_ajax: del headers_ajax['Content-Type']

        # 4. Search and Get Popup Data
        res = session.get(ctrl_url, params={'data': f"{user_input}_0__{cbo_logic}_2__1_", 'action': 'create_challan_search_list_view'}, headers=headers_ajax)
        mid = re.search(r"js_set_value\((\d+)\)", res.text)
        if not mid: return {"status": "error", "message": "❌ Invalid Challan / No Data"}
        sys_id = mid.group(1)

        res_pop = session.post(ctrl_url, params={'data': sys_id, 'action': 'populate_data_from_challan_popup'}, data={'rndval': int(time.time()*1000)}, headers=headers_common)
        
        def get_val(id_name, text):
            pattern = re.escape(id_name) + r".*?\.val\(\s*['\"]?([^'\")]+)['\"]?\s*\)"
            m = re.search(pattern, text)
            return m.group(1).strip() if m else '0'

        source = get_val("cbo_source", res_pop.text)
        emb_company = get_val("cbo_emb_company", res_pop.text)
        line = get_val("cbo_line_no", res_pop.text)
        location = get_val("cbo_location", res_pop.text)
        floor = get_val("cbo_floor", res_pop.text)

        # Validation
        forbidden = ['0', '00', '', 'undefined', 'null']
        missing_fields = []
        if source in forbidden: missing_fields.append("Source")
        if emb_company in forbidden: missing_fields.append("Emb Company")
        if line in forbidden: missing_fields.append("Line No")
        if location in forbidden: missing_fields.append("Location")
        
        if missing_fields:
            return {"status": "error", "message": f"⚠️ Missing/Zero: {', '.join(missing_fields)}"}

        # Bundles Extraction
        res_bun = session.get(ctrl_url, params={'data': sys_id, 'action': 'bundle_nos'}, headers=headers_ajax)
        raw_bun = res_bun.text.split("**")[0]
        if not raw_bun: return {"status": "error", "message": "❌ Empty Bundle List"}

        res_tbl = session.get(ctrl_url, params={'data': f"{raw_bun}**0**{sys_id}**{cbo_logic}**{line}", 'action': 'populate_bundle_data_update'}, headers=headers_ajax)
        rows = res_tbl.text.split('<tr')
        b_data = []
        for r in rows:
            if 'id="tr_' not in r: continue
            def get_row_val(pat, txt):
                m = re.search(pat, txt)
                return m.group(1) if m else '0'
            
            b_data.append({
                'barcodeNo': get_row_val(r"title=\"(\d+)\"", r), 
                'bundleNo': get_row_val(r"id=\"bundle_\d+\"[^>]*>([^<]+)", r),
                'orderId': get_row_val(r"name=\"orderId\[\]\".*?value=\"(\d+)\"", r), 
                'gmtsitemId': get_row_val(r"name=\"gmtsitemId\[\]\".*?value=\"(\d+)\"", r),
                'countryId': get_row_val(r"name=\"countryId\[\]\".*?value=\"(\d+)\"", r), 
                'colorId': get_row_val(r"name=\"colorId\[\]\".*?value=\"(\d+)\"", r),
                'sizeId': get_row_val(r"name=\"sizeId\[\]\".*?value=\"(\d+)\"", r), 
                'colorSizeId': get_row_val(r"name=\"colorSizeId\[\]\".*?value=\"(\d+)\"", r),
                'qty': get_row_val(r"name=\"qty\[\]\".*?value=\"(\d+)\"", r), 
                'dtlsId': get_row_val(r"name=\"dtlsId\[\]\".*?value=\"(\d+)\"", r),
                'cutNo': get_row_val(r"name=\"cutNo\[\]\".*?value=\"([^\"]+)\"", r), 
                'isRescan': get_row_val(r"name=\"isRescan\[\]\".*?value=\"(\d+)\"", r)
            })

        # 5. Save Payload
        bd_zone = timezone(timedelta(hours=6))
        now_bd = datetime.now(bd_zone)
        
        # যদি আজ শুক্রবার (weekday() == 4) হয়, তাহলে গতকালের তারিখ ব্যবহার করো
        if now_bd.weekday() == 4:  # শুক্রবার = 4 (Monday=0, Friday=4)
            save_date = now_bd - timedelta(days=1)  # গতকালের তারিখ (বৃহস্পতিবার)
        else:
            save_date = now_bd  # অন্যান্য দিনে আজকের তারিখ
        
        fmt_date = save_date.strftime("%d-%b-%Y")
        curr_time = now_bd.strftime("%H:%M")
        
        payload = {
            'action': 'save_update_delete', 'operation': '0', 'tot_row': str(len(b_data)),
            'garments_nature': "'2'", 'cbo_company_name': f"'{cbo_logic}'", 'sewing_production_variable': "'3'",
            'cbo_source': f"'{source}'",          
            'cbo_emb_company': f"'{emb_company}'", 
            'cbo_location': f"'{location}'",      
            'cbo_floor': f"'{floor}'",            
            'txt_issue_date': f"'{fmt_date}'", 'txt_organic': "''", 'txt_system_id': "''", 'delivery_basis': "'3'",
            'txt_challan_no': "''", 
            'cbo_line_no': f"'{line}'",           
            'cbo_shift_name': "'0'",
            'cbo_working_company_name': "'0'", 'cbo_working_location': "'0'", 
            'txt_remarks': "''", 
            'txt_reporting_hour': f"'{curr_time}'"
        }

        for i, b in enumerate(b_data, 1):
            payload[f'bundleNo_{i}'] = b['bundleNo']; payload[f'orderId_{i}'] = b['orderId']
            payload[f'gmtsitemId_{i}'] = b['gmtsitemId']; payload[f'countryId_{i}'] = b['countryId']
            payload[f'colorId_{i}'] = b['colorId']; payload[f'sizeId_{i}'] = b['sizeId']
            payload[f'inseamId_{i}'] = '0'; payload[f'colorSizeId_{i}'] = b['colorSizeId']
            payload[f'qty_{i}'] = b['qty']; payload[f'dtlsId_{i}'] = b['dtlsId']
            payload[f'cutNo_{i}'] = b['cutNo']; payload[f'isRescan_{i}'] = b['isRescan']
            payload[f'barcodeNo_{i}'] = b['barcodeNo']; payload[f'cutMstIdNo_{i}'] = '0'; payload[f'cutNumPrefixNo_{i}'] = '0'

        headers_save = headers_common.copy()
        headers_save['Referer'] = f"{base_url}/production/bundle_wise_sewing_input.php?permission=1_1_2_1"
        
        save_res = session.post(f"{base_url}/production/requires/bundle_wise_sewing_input_controller.php", data=payload, headers=headers_save)
        
        if "**" in save_res.text:
            parts = save_res.text.split('**')
            code = parts[0].strip()
            
            if code == "0":
                new_sys_id = parts[1]
                new_challan = parts[2] if len(parts) > 2 else "Sewing Challan"
                u1 = f"{base_url}/production/requires/bundle_wise_sewing_input_controller.php?data=1*{new_sys_id}*3*%E2%9D%8F%20Bundle%20Wise%20Sewing%20Input*1*undefined*undefined*undefined&action=emblishment_issue_print_13"
                u2 = f"{base_url}/production/requires/bundle_wise_sewing_input_controller.php?data=1*{new_sys_id}*3*%E2%9D%8F%20Bundle%20Wise%20Sewing%20Input*undefined*undefined*undefined*1&action=sewing_input_challan_print_5"
                return {"status": "success", "challan_no": new_challan, "system_id": new_sys_id, "report1_url": u1, "report2_url": u2}
            elif code == "20": return {"status": "error", "message": "❌ Bundle Already Scanned!"}
            elif code == "10": return {"status": "error", "message": "❌ Validation Error (10)."}
            else: return {"status": "error", "message": f"Server Error Code: {code}"}
        
        return {"status": "error", "message": f"Save Failed: {save_res.status_code}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- ROUTES ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    if not data or 'challan' not in data or 'company_id' not in data:
        return jsonify({"status": "error", "message": "Missing Data"})
    
    client_ua = request.headers.get('User-Agent')
    return jsonify(process_data(data['challan'], client_ua, data['company_id']))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)
