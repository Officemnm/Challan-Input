from flask import Flask, request, jsonify, render_template_string, send_from_directory
import requests
import re
import time
import os
import random
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# --- CONFIGURATION ---
app = Flask(__name__)
REPORT_DIR = "reports"
if not os.path.exists(REPORT_DIR):
    os.makedirs(REPORT_DIR)

# --- MODERN UI TEMPLATE ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Production Automation | MnM Office</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;600;700&display=swap" rel="stylesheet">
    
    <style>
        :root {
            --primary-gradient: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            --glass-bg: rgba(255, 255, 255, 0.95);
            --success-color: #10b981;
            --error-color: #ef4444;
        }

        body {
            font-family: 'Outfit', sans-serif;
            background-image: url('https://images.unsplash.com/photo-1497366216548-37526070297c?auto=format&fit=crop&w=1920&q=80');
            background-size: cover;
            background-position: center;
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            margin: 0;
        }

        .backdrop-overlay {
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.4);
            backdrop-filter: blur(8px);
            z-index: -1;
        }

        .main-card {
            background: var(--glass-bg);
            border-radius: 24px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.2);
            width: 100%;
            max-width: 480px;
            overflow: hidden;
            border: 1px solid rgba(255,255,255,0.5);
            transform: translateY(0);
            transition: transform 0.3s ease;
        }

        .card-header-custom {
            background: var(--primary-gradient);
            padding: 40px 30px;
            text-align: center;
            color: white;
            position: relative;
            overflow: hidden;
        }

        .card-header-custom::after {
            content: '';
            position: absolute;
            top: -50%; left: -50%; width: 200%; height: 200%;
            background: radial-gradient(circle, rgba(255,255,255,0.1) 0%, transparent 60%);
            animation: rotate 10s linear infinite;
        }

        @keyframes rotate { from {transform: rotate(0deg);} to {transform: rotate(360deg);} }

        .app-title { font-weight: 700; letter-spacing: 1px; font-size: 1.5rem; margin-bottom: 5px; }
        .app-subtitle { font-size: 0.9rem; opacity: 0.9; font-weight: 300; }

        .card-body-custom { padding: 35px 30px; }

        .form-floating > .form-control {
            border-radius: 12px;
            border: 2px solid #e2e8f0;
            height: 60px;
            font-size: 1.2rem;
            font-weight: 600;
            letter-spacing: 2px;
            color: #2d3748;
        }
        
        .form-floating > .form-control:focus {
            border-color: #764ba2;
            box-shadow: 0 0 0 4px rgba(118, 75, 162, 0.1);
        }

        .btn-process {
            background: var(--primary-gradient);
            border: none;
            height: 55px;
            border-radius: 12px;
            font-weight: 600;
            font-size: 1.1rem;
            letter-spacing: 0.5px;
            margin-top: 25px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s;
        }

        .btn-process:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(118, 75, 162, 0.3);
        }

        .btn-process:active { transform: translateY(0); }

        /* Result Styles */
        .result-container {
            display: none;
            margin-top: 30px;
            animation: slideUp 0.5s ease-out;
        }

        .status-box {
            padding: 20px;
            border-radius: 16px;
            text-align: center;
            position: relative;
        }

        .status-success {
            background: #ecfdf5;
            border: 2px solid #10b981;
            color: #065f46;
        }

        .status-error {
            background: #fff5f5;
            border: 2px solid #fc8181;
            color: #c53030;
        }

        .challan-badge {
            background: white;
            padding: 8px 20px;
            border-radius: 50px;
            font-weight: 700;
            font-size: 1.2rem;
            color: #333;
            box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            display: inline-block;
            margin: 15px 0;
            border: 1px dashed #cbd5e0;
        }

        .action-buttons {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 20px;
        }

        .btn-report {
            padding: 12px;
            border-radius: 10px;
            font-size: 0.9rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            justify-content: center;
            text-decoration: none;
            transition: all 0.2s;
        }

        .btn-report-1 { background: white; border: 2px solid #3b82f6; color: #3b82f6; }
        .btn-report-1:hover { background: #3b82f6; color: white; }

        .btn-report-2 { background: #1f2937; border: 2px solid #1f2937; color: white; }
        .btn-report-2:hover { background: #374151; border-color: #374151; }

        /* Loader */
        .loader-overlay {
            display: none;
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(255,255,255,0.8);
            z-index: 10;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            border-radius: 24px;
        }
        
        .spinner-custom {
            width: 50px; height: 50px;
            border: 5px solid #f3f3f3;
            border-top: 5px solid #764ba2;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        @keyframes slideUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }

        .footer {
            text-align: center;
            margin-top: 30px;
            font-size: 0.8rem;
            color: #718096;
        }
    </style>
</head>
<body>

    <div class="backdrop-overlay"></div>

    <div class="main-card">
        <div class="loader-overlay" id="mainLoader">
            <div class="spinner-custom mb-3"></div>
            <h6 class="text-muted fw-bold">PROCESSING DATA...</h6>
            <small class="text-muted">Please wait, connecting to ERP</small>
        </div>

        <div class="card-header-custom">
            <div class="app-title"><i class="fa-solid fa-microchip me-2"></i>SEWING INPUT</div>
            <div class="app-subtitle">Automated Production System v4.0</div>
        </div>

        <div class="card-body-custom">
            <form id="entryForm">
                <div class="form-floating mb-2">
                    <input type="number" class="form-control" id="challanInput" placeholder="Challan No" required autocomplete="off">
                    <label for="challanInput"><i class="fa-solid fa-barcode me-2"></i>SCAN / ENTER CHALLAN</label>
                </div>
                
                <button type="submit" class="btn btn-primary w-100 btn-process">
                    START PROCESS <i class="fa-solid fa-rocket ms-2"></i>
                </button>
            </form>

            <div id="successArea" class="result-container">
                <div class="status-box status-success">
                    <i class="fa-solid fa-check-circle fa-3x mb-2"></i>
                    <h4 class="fw-bold m-0">SUCCESS!</h4>
                    <div class="challan-badge" id="successChallan">---</div>
                    <div class="text-muted small mb-3" id="systemIdTxt">ID: ---</div>

                    <div class="action-buttons">
                        <a href="#" id="linkRep1" target="_blank" class="btn-report btn-report-1">
                            <i class="fa-solid fa-file-invoice me-2"></i> Bundle Report
                        </a>
                        <a href="#" id="linkRep2" target="_blank" class="btn-report btn-report-2">
                            <i class="fa-solid fa-print me-2"></i> Print Challan
                        </a>
                    </div>
                    
                    <button onclick="resetUI()" class="btn btn-link text-muted text-decoration-none mt-3 btn-sm">
                        <i class="fa-solid fa-rotate-left me-1"></i> Process Another
                    </button>
                </div>
            </div>

            <div id="errorArea" class="result-container">
                <div class="status-box status-error">
                    <div class="mb-2"><i class="fa-solid fa-triangle-exclamation fa-3x"></i></div>
                    <h5 class="fw-bold">FAILED</h5>
                    <p class="small mb-0 fw-bold" id="errorMsg">Unknown Error</p>
                    <button onclick="resetUI()" class="btn btn-danger btn-sm mt-3 px-4 rounded-pill">TRY AGAIN</button>
                </div>
            </div>

            <div class="footer">
                &copy; 2025 MnM Office Automation
            </div>
        </div>
    </div>

    <script>
        const form = document.getElementById('entryForm');
        const loader = document.getElementById('mainLoader');
        const successArea = document.getElementById('successArea');
        const errorArea = document.getElementById('errorArea');
        const input = document.getElementById('challanInput');

        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const val = input.value;
            if(!val) return;

            // Show Loader
            loader.style.display = 'flex';
            successArea.style.display = 'none';
            errorArea.style.display = 'none';
            input.blur();

            try {
                const req = await fetch('/process', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({challan: val})
                });
                const res = await req.json();

                if(res.status === 'success') {
                    document.getElementById('successChallan').innerText = res.challan_no;
                    document.getElementById('systemIdTxt').innerText = "System ID: " + res.system_id;
                    
                    // Set Report Links (Opens in New Tab)
                    document.getElementById('linkRep1').href = `/reports/${res.report1}`;
                    document.getElementById('linkRep2').href = `/reports/${res.report2}`;
                    
                    successArea.style.display = 'block';
                } else {
                    document.getElementById('errorMsg').innerText = res.message;
                    errorArea.style.display = 'block';
                }
            } catch (err) {
                document.getElementById('errorMsg').innerText = "Server Connection Error";
                errorArea.style.display = 'block';
            } finally {
                loader.style.display = 'none';
            }
        });

        function resetUI() {
            input.value = '';
            successArea.style.display = 'none';
            errorArea.style.display = 'none';
            input.focus();
        }
    </script>
</body>
</html>
"""

# --- BACKEND LOGIC ---
def process_data(user_input):
    base_url = "http://180.92.235.190:8022/erp"
    
    headers_common = {
        'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Mobile Safari/537.36',
        'Content-Type': 'application/x-www-form-urlencoded',
        'Origin': 'http://180.92.235.190:8022',
        'Referer': f"{base_url}/login.php"
    }

    session = requests.Session()
    retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retry)
    session.mount("http://", adapter)

    # 1. Login
    try:
        session.post(f"{base_url}/login.php", data={'txt_userid': 'input1.clothing-cutting', 'txt_password': '123456', 'submit': 'Login'}, headers=headers_common)
    except Exception as e:
        return {"status": "error", "message": "Login Failed"}

    # 2. Session Activation
    headers_menu = headers_common.copy()
    headers_menu['Referer'] = f"{base_url}/production/bundle_wise_sewing_input.php?permission=1_1_2_1"
    try:
        session.get(f"{base_url}/tools/valid_user_action.php?menuid=724", headers=headers_menu)
        session.get(f"{base_url}/includes/common_functions_for_js.php?data=724_7_406&action=create_menu_session", headers=headers_menu)
    except: pass

    # 3. Fetch Data
    cbo_logic = '1'
    if user_input.startswith('4'): cbo_logic = '4'
    elif user_input.startswith('3'): cbo_logic = '2'

    ctrl_url = f"{base_url}/production/requires/bundle_wise_cutting_delevar_to_input_controller.php"
    headers_ajax = headers_common.copy()
    headers_ajax['X-Requested-With'] = 'XMLHttpRequest'
    if 'Content-Type' in headers_ajax: del headers_ajax['Content-Type']

    try:
        # Search
        res = session.get(ctrl_url, params={'data': f"{user_input}_0__{cbo_logic}_2__1_", 'action': 'create_challan_search_list_view'}, headers=headers_ajax)
        mid = re.search(r"js_set_value\((\d+)\)", res.text)
        if not mid: return {"status": "error", "message": "❌ Invalid Challan / No Data Found"}
        sys_id = mid.group(1)

        # Extract Header
        res_pop = session.post(ctrl_url, params={'data': sys_id, 'action': 'populate_data_from_challan_popup'}, data={'rndval': int(time.time()*1000)}, headers=headers_common)
        
        def get_val(pat, txt, d='0'):
            m = re.search(pat, txt)
            return m.group(1) if m else d

        floor = get_val(r"\$\('#cbo_floor'\)\.val\('([^']*)'\)", res_pop.text)
        line = get_val(r"\$\('#cbo_line_no'\)\.val\('([^']*)'\)", res_pop.text)
        
        # Date Logic
        r_date = get_val(r"\$\('#txt_issue_date'\)\.val\('([^']*)'\)", res_pop.text, datetime.now().strftime("%d-%b-%Y"))
        try: fmt_date = datetime.strptime(r_date, "%d-%m-%Y").strftime("%d-%b-%Y")
        except: fmt_date = r_date

        # Bundles
        res_bun = session.get(ctrl_url, params={'data': sys_id, 'action': 'bundle_nos'}, headers=headers_ajax)
        raw_bun = res_bun.text.split("**")[0]
        if not raw_bun: return {"status": "error", "message": "❌ No Bundles Found"}

        res_tbl = session.get(ctrl_url, params={'data': f"{raw_bun}**0**{sys_id}**{cbo_logic}**{line}", 'action': 'populate_bundle_data_update'}, headers=headers_ajax)
        
        rows = res_tbl.text.split('<tr')
        b_data = []
        for r in rows:
            if 'id="tr_' not in r: continue
            b_data.append({
                'barcodeNo': get_val(r"title=\"(\d+)\"", r), 'bundleNo': get_val(r"id=\"bundle_\d+\"[^>]*>([^<]+)", r, "Unknown"),
                'orderId': get_val(r"name=\"orderId\[\]\".*?value=\"(\d+)\"", r), 'gmtsitemId': get_val(r"name=\"gmtsitemId\[\]\".*?value=\"(\d+)\"", r),
                'countryId': get_val(r"name=\"countryId\[\]\".*?value=\"(\d+)\"", r), 'colorId': get_val(r"name=\"colorId\[\]\".*?value=\"(\d+)\"", r),
                'sizeId': get_val(r"name=\"sizeId\[\]\".*?value=\"(\d+)\"", r), 'colorSizeId': get_val(r"name=\"colorSizeId\[\]\".*?value=\"(\d+)\"", r),
                'qty': get_val(r"name=\"qty\[\]\".*?value=\"(\d+)\"", r), 'dtlsId': get_val(r"name=\"dtlsId\[\]\".*?value=\"(\d+)\"", r),
                'cutNo': get_val(r"name=\"cutNo\[\]\".*?value=\"([^\"]+)\"", r), 'isRescan': get_val(r"name=\"isRescan\[\]\".*?value=\"(\d+)\"", r)
            })

        # Save
        curr_time = datetime.now().strftime("%H:%M")
        payload = {
            'action': 'save_update_delete', 'operation': '0', 'tot_row': str(len(b_data)),
            'garments_nature': "'2'", 'cbo_company_name': f"'{cbo_logic}'", 'sewing_production_variable': "'3'",
            'cbo_source': "'1'", 'cbo_emb_company': "'2'", 'cbo_location': "'2'", 'cbo_floor': f"'{floor}'",
            'txt_issue_date': f"'{fmt_date}'", 'txt_organic': "''", 'txt_system_id': "''", 'delivery_basis': "'3'",
            'txt_challan_no': "''", 'cbo_line_no': f"'{line}'", 'cbo_shift_name': "'0'",
            'cbo_working_company_name': "'0'", 'cbo_working_location': "'0'", 'txt_remarks': "''", 'txt_reporting_hour': f"'{curr_time}'"
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
                
                # Fetch Reports
                headers_rep = headers_common.copy()
                headers_rep['Upgrade-Insecure-Requests'] = '1'
                
                # Report 1
                d1 = f"1*{new_sys_id}*{cbo_logic}*%E2%9D%8F%20Bundle%20Wise%20Sewing%20Input*1*undefined*undefined*undefined"
                rep1 = session.get(ctrl_url, params={'data': d1, 'action': 'emblishment_issue_print_13'}, headers=headers_rep)
                f1 = f"Bundle_{new_sys_id}.html"
                with open(os.path.join(REPORT_DIR, f1), "w", encoding="utf-8") as f: f.write(rep1.text)
                
                # Report 2
                d2 = f"1*{new_sys_id}*{cbo_logic}*%E2%9D%8F%20Bundle%20Wise%20Sewing%20Input*undefined*undefined*undefined*1"
                rep2 = session.get(ctrl_url, params={'data': d2, 'action': 'sewing_input_challan_print_5'}, headers=headers_rep)
                f2 = f"Challan_{new_sys_id}.html"
                with open(os.path.join(REPORT_DIR, f2), "w", encoding="utf-8") as f: f.write(rep2.text)

                return {
                    "status": "success",
                    "challan_no": new_challan,
                    "system_id": new_sys_id,
                    "report1": f1,
                    "report2": f2
                }
            
            elif code == "20": return {"status": "error", "message": "❌ সার্ভার সমস্যা / বান্ডিল অলরেডি পান্স করা হয়েছে!"}
            elif code == "10": return {"status": "error", "message": "❌ Validation Error (10). Check Line/Floor."}
            else: return {"status": "error", "message": f"Server Error Code: {code}"}
        
        return {"status": "error", "message": f"Save Failed: {save_res.status_code}"}

    except Exception as e:
        return {"status": "error", "message": str(e)}

# --- APP ROUTES ---
@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/process', methods=['POST'])
def process():
    data = request.json
    if not data or 'challan' not in data: return jsonify({"status": "error", "message": "No Data"})
    return jsonify(process_data(data['challan']))

@app.route('/reports/<path:filename>')
def serve_report(filename):
    return send_from_directory(REPORT_DIR, filename)

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=10000)

