from flask import Flask, request, render_template_string
import csv
import os

app = Flask(__name__)

CSV_FILE = "tnea_2025_cutoff_vs_round1_vacancy_clean_no_2020_2021.csv"

CATEGORIES = ["OC", "BC", "BCM", "MBC", "SC", "SCA", "ST"]

DISTRICT_LIST = [
    "Ariyalur",
    "Chengalpattu",
    "Chennai",
    "Coimbatore",
    "Cuddalore",
    "Dharmapuri",
    "Dindigul",
    "Erode",
    "Kallakurichi",
    "Kanchipuram",
    "Kanyakumari",
    "Karur",
    "Krishnagiri",
    "Madurai",
    "Mayiladuthurai",
    "Nagapattinam",
    "Namakkal",
    "Nilgiris",
    "Perambalur",
    "Pudukkottai",
    "Ramanathapuram",
    "Salem",
    "Sivagangai",
    "Thanjavur",
    "Tenkasi",
    "Theni",
    "Thiruvallur",
    "Thiruvannamalai",
    "Thoothukudi",
    "Tirunelveli",
    "Tiruppur",
    "Trichy",
    "Vellore",
    "Virudhunagar"
]

COMPUTER_FAMILY = [
    "CS", "CM", "IT", "AD", "AM", "AI", "AL", "CB", "SC", "CD",
    "CI", "CW", "CY", "CO", "CF", "CG", "CN", "AT"
]

ECE_FAMILY = ["EC", "EM", "EA", "EI", "EL", "EV", "EX"]

PRIORITY_COLLEGES = [
    "CEG",
    "COLLEGE OF ENGINEERING GUINDY",
    "PSG COLLEGE OF TECHNOLOGY",
    "PSG INSTITUTE OF TECHNOLOGY",
    "SAVEETHA",
    "MADRAS INSTITUTE OF TECHNOLOGY",
    "MIT CAMPUS",
    "CHENNAI INSTITUTE OF TECHNOLOGY",
    "COIMBATORE INSTITUTE OF TECHNOLOGY",
    "NEW PRINCE SHRI BHAVANI",
    "KUMARAGURU",
    "GOVERNMENT COLLEGE OF ENGINEERING SALEM",
    "GOVERNMENT COLLEGE OF ENGINEERING KARUPPUR",
    "THIAGARAJAR",
    "RAJALAKSHMI",
    "GOVERNMENT COLLEGE OF TECHNOLOGY",
    "ALAGAPPA CHETTIAR",
    "SRI KRISHNA",
    "PRINCE DR K VASUDEVAN",
    "PRINCE SHRI VENKATESHWARA",
    "SRI ESHWAR",
    "JCT",
    "THANTHAI PERIYAR",
    "LOYOLA",
    "LOYOLA-ICAM",
    "DHAANISH",
    "KARPAGAM",
    "ST. JOSEPH'S INSTITUTE OF TECHNOLOGY",
    "ST JOSEPH'S INSTITUTE OF TECHNOLOGY",
    "ST JOSEPHS INSTITUTE OF TECHNOLOGY",
    "NATIONAL ENGINEERING COLLEGE",
    "R M K",
    "RMK",
    "R M D",
    "RMD",
    "MEPCO",
    "KONGU",
    "SAIRAM",
    "SRI SAI RAM",
    "SRM VALLIAMMAI",
    "VALLIAMMAI",
    "BANNARI",
    "KPR",
    "PANIMALAR",
    "FRANCIS XAVIER",
    "ST XAVIER",
    "KALAIGNAR KARUNANIDHI",
    "KIT",
    "EASWARI",
    "SRM EASWARI",
    "GOVERNMENT COLLEGE OF ENGINEERING ERODE",
    "GOVERNMENT COLLEGE OF ENGINEERING TIRUNELVELI",
    "GOVERNMENT COLLEGE OF ENGINEERING THENI",
    "ROHINI",
    "ARUNACHALA HITECH",
    "S.A. ENGINEERING",
    "SA ENGINEERING"
]


def clean(value):
    if value is None:
        return ""
    return str(value).strip()


def get_first(row, names):
    for name in names:
        if name in row and clean(row.get(name)) != "":
            return clean(row.get(name))
    return ""


def to_float(value):
    value = clean(value)
    if value in ["", "-", "NA", "N/A", "None", "nan"]:
        return None
    try:
        return float(value)
    except ValueError:
        return None


def to_int(value):
    number = to_float(value)
    if number is None:
        return None
    return int(number)


def format_number(value):
    if value is None:
        return "-"
    try:
        value = float(value)
        if value.is_integer():
            return str(int(value))
        return str(value)
    except:
        return str(value)


def is_priority_college(college_name):
    name = college_name.upper()
    return any(priority in name for priority in PRIORITY_COLLEGES)


def priority_rank(college_name):
    name = college_name.upper()
    for index, priority in enumerate(PRIORITY_COLLEGES):
        if priority in name:
            return index
    return 9999


def calculate_cutoff(physics, chemistry, maths):
    return maths + (physics / 2) + (chemistry / 2)


def predict_round(cutoff):
    if 179 <= cutoff <= 200:
        return "Round 1", "🌟 You are in a strong range. Stay calm and focus on choice order — this is where strategy matters."
    elif 142 <= cutoff <= 178.9:
        return "Round 2", "🌸 You are in the serious strategy zone. Cutoff alone is not enough here, so I’ll check vacancy reality also."
    elif 77 <= cutoff <= 141.9:
        return "Round 3", "🧸 Your score still has value. Smart backup choices matter a lot here, so don’t panic."
    return "Outside usual round range", "Please recheck your marks. TNEA cutoff should usually be between 0 and 200."


def subject_praise(maths, physics, chemistry):
    messages = []

    if maths >= 90:
        messages.append("✨ Your Maths mark is strong. That shows real problem-solving ability — engineering needs exactly that.")
    elif maths >= 80:
        messages.append("🌷 Your Maths mark is good. You already have a nice base for technical subjects.")
    else:
        messages.append("🫶 Marks are not your full story. A smart branch and college order can still protect your future.")

    if physics >= 90:
        messages.append("💫 Your Physics mark is also strong. That’s a nice sign for technical understanding.")

    if chemistry >= 90:
        messages.append("🦋 Your Chemistry mark is strong too. That helped your cutoff beautifully.")

    return messages


def chance_status(user_cutoff, required_cutoff):
    if required_cutoff is None:
        return "No cutoff data", "⚪", 999

    difference = user_cutoff - required_cutoff

    if difference >= 0:
        return "Cutoff Safe", "🟢", abs(difference)
    elif difference >= -5:
        return "Cutoff Close", "🟡", abs(difference)
    elif difference >= -10:
        return "Cutoff Dream", "🔴", abs(difference)
    return "Very Difficult", "⚫", abs(difference)


def branch_matches(branch_code, branch_name, preferred_branch, branch_mode):
    preferred_branch = preferred_branch.strip().upper()
    branch_code = branch_code.strip().upper()
    branch_name = branch_name.strip().upper()

    if preferred_branch in ["", "ANY"]:
        return True

    if branch_mode == "exact":
        if preferred_branch == "CSE":
            preferred_branch = "CS"
        if preferred_branch == "ECE":
            preferred_branch = "EC"
        return preferred_branch == branch_code

    if preferred_branch in ["CS", "CSE"]:
        return branch_code in COMPUTER_FAMILY or "COMPUTER" in branch_name or "INFORMATION TECHNOLOGY" in branch_name

    if preferred_branch in ["EC", "ECE"]:
        return branch_code in ECE_FAMILY or "ELECTRONICS" in branch_name or "COMMUNICATION" in branch_name

    return preferred_branch == branch_code or preferred_branch in branch_name


def district_matches(row_district, college_name, selected_district):
    selected_district = selected_district.strip().upper()

    if selected_district in ["", "ANY"]:
        return True

    text = (row_district + " " + college_name).upper()

    district_aliases = {
        "TRICHY": ["TRICHY", "TIRUCHIRAPPALLI"],
        "THOOTHUKUDI": ["THOOTHUKUDI", "TUTICORIN"],
        "NILGIRIS": ["NILGIRIS", "NILGIRI"],
        "KANYAKUMARI": ["KANYAKUMARI", "NAGERCOIL"],
        "KANCHIPURAM": ["KANCHIPURAM", "KANCHEEPURAM"],
        "CHENGALPATTU": ["CHENGALPATTU", "CHENGALPET"],
        "THIRUVALLUR": ["THIRUVALLUR", "TIRUVALLUR"],
        "TIRUNELVELI": ["TIRUNELVELI", "THIRUNELVELI"],
        "THIRUVANNAMALAI": ["THIRUVANNAMALAI", "TIRUVANNAMALAI"],
        "PUDUKKOTTAI": ["PUDUKKOTTAI", "PUDUKOTTAI"],
        "MAYILADUTHURAI": ["MAYILADUTHURAI", "MAYILADUTURAI"]
    }

    aliases = district_aliases.get(selected_district, [selected_district])

    for alias in aliases:
        if alias in text:
            return True

    return False


def gender_theme(gender):
    gender = gender.lower().strip()

    if gender == "female":
        return "theme-female"
    elif gender == "male":
        return "theme-male"
    return "theme-neutral"


def load_master_data():
    data = []

    if not os.path.exists(CSV_FILE):
        return data

    with open(CSV_FILE, "r", encoding="utf-8-sig", newline="") as file:
        reader = csv.DictReader(file)

        for row in reader:
            category = get_first(row, ["category", "Category"]).upper()

            if category not in CATEGORIES:
                continue

            college_code = get_first(row, ["college_code", "COLLEGE CODE", "College Code"])
            college_name = get_first(row, ["college_name", "COLLEGE NAME", "College Name"])
            district = get_first(row, ["district", "district_from_cutoff_pdf", "District"])

            branch_code = get_first(row, ["branch_code", "BRANCH CODE", "Branch Code"]).upper()
            branch_name = get_first(row, ["branch_name", "BRANCH NAME", "Branch Name"])

            cutoff = to_float(get_first(row, [
                "cutoff_2025_max_if_duplicates",
                "cutoff_2025",
                "cutoff",
                "Cutoff"
            ]))

            vacancy_r1 = to_int(get_first(row, [
                "vacancy_after_round1_2025",
                "round1_vacancy_2025",
                "vacancy_after_round1",
                "Vacancy After Round 1"
            ]))

            if cutoff is None:
                continue

            data.append({
                "college_code": college_code,
                "college_name": college_name,
                "district": district,
                "branch_code": branch_code,
                "branch_name": branch_name if branch_name else f"Branch code {branch_code}",
                "category": category,
                "cutoff": cutoff,
                "vacancy_after_round1": vacancy_r1,
                "priority": is_priority_college(college_name),
                "priority_rank": priority_rank(college_name)
            })

    return data


def get_districts(data):
    return DISTRICT_LIST


def make_result(row, user_cutoff, student_round):
    cutoff_status, cutoff_icon, close_gap = chance_status(user_cutoff, row["cutoff"])
    vacancy = row["vacancy_after_round1"]
    difference = None if row["cutoff"] is None else round(user_cutoff - row["cutoff"], 2)

    final_section = "dream"
    final_label = "🎯 Dream / Needs backup"
    sneaky_note = "🎯 This is a dream-style option. Keep it only with proper backups."

    if student_round == "Round 1":
        if cutoff_status == "Cutoff Safe":
            final_section = "safe"
            final_label = "🟢 Round 1 Safe by cutoff trend"
            sneaky_note = "💎 Cutoff trend supports this. Still verify final choice list carefully."
        elif cutoff_status == "Cutoff Close":
            final_section = "successor"
            final_label = "🟡 Round 1 Good Try"
            sneaky_note = "🌷 Close option. Worth trying, but keep safe backups."
        elif cutoff_status == "Cutoff Dream":
            final_section = "dream"
            final_label = "🔴 Round 1 Dream"
            sneaky_note = "🎯 Nice dream choice, but don’t depend only on this."

    elif student_round == "Round 2":
        if cutoff_status == "Cutoff Safe" and vacancy is not None and vacancy > 0:
            final_section = "safe"
            final_label = "🟢 Realistic Safe"
            sneaky_note = "💎 Cutoff supports it and vacancy after Round 1 existed. This is a serious option."
        elif cutoff_status == "Cutoff Close" and vacancy is not None and vacancy > 0:
            final_section = "successor"
            final_label = "🟡 Successor / Good Try"
            sneaky_note = "🌷 Cutoff is close and vacancy existed. Worth placing with strategy."
        elif cutoff_status in ["Cutoff Safe", "Cutoff Close"] and vacancy == 0:
            final_section = "risky"
            final_label = "⚠️ Risky despite cutoff"
            sneaky_note = "👀 Cutoff says possible, but vacancy after Round 1 was zero. Don’t depend on this alone."
        elif cutoff_status in ["Cutoff Dream", "Very Difficult"]:
            final_section = "dream"
            final_label = "🎯 Dream"
            sneaky_note = "🎯 Dream option. Keep only if you have safe choices below."
        else:
            final_section = "risky"
            final_label = "⚠️ Needs vacancy check"
            sneaky_note = "👀 Data is incomplete here. Verify before depending on it."

    else:
        if cutoff_status == "Cutoff Safe":
            final_section = "successor"
            final_label = "🟡 Cutoff Safe, but Round 3 vacancy needed"
            sneaky_note = "🧸 Cutoff supports it, but for Round 3 we need after Round 2 vacancy for full reality."
        elif cutoff_status == "Cutoff Close":
            final_section = "risky"
            final_label = "⚠️ Close, but Round 3 uncertain"
            sneaky_note = "👀 This needs Round 2 vacancy data before trusting."
        else:
            final_section = "dream"
            final_label = "🎯 Dream / uncertain"
            sneaky_note = "🎯 Keep backup choices strongly."

    return {
        **row,
        "cutoff_status": cutoff_status,
        "cutoff_icon": cutoff_icon,
        "close_gap": round(close_gap, 2) if close_gap != 999 else 999,
        "difference": difference,
        "final_section": final_section,
        "final_label": final_label,
        "sneaky_note": sneaky_note
    }


def sort_results(results):
    return sorted(
        results,
        key=lambda x: (
            x["close_gap"],
            0 if (x["vacancy_after_round1"] is not None and x["vacancy_after_round1"] > 0) else 1,
            0 if x["priority"] else 1,
            x["priority_rank"]
        )
    )


def explore_options(data, user_cutoff, category, preferred_branch, student_round, selected_district, branch_mode):
    safe, successor, risky, dream = [], [], [], []

    for row in data:
        if row["category"] != category:
            continue

        if not district_matches(row["district"], row["college_name"], selected_district):
            continue

        if not branch_matches(row["branch_code"], row["branch_name"], preferred_branch, branch_mode):
            continue

        result = make_result(row, user_cutoff, student_round)

        if result["final_section"] == "safe":
            safe.append(result)
        elif result["final_section"] == "successor":
            successor.append(result)
        elif result["final_section"] == "risky":
            risky.append(result)
        else:
            dream.append(result)

    return sort_results(safe), sort_results(successor), sort_results(risky), sort_results(dream)


def dream_college_check(data, user_cutoff, category, college_code, student_round):
    results = []

    for row in data:
        if row["category"] != category:
            continue

        if row["college_code"] != college_code:
            continue

        results.append(make_result(row, user_cutoff, student_round))

    return sort_results(results)


def pookie_tip(mode, preferred_branch, student_round, branch_mode):
    if mode == "dream":
        return "🎯 Pookie safety tip: College code is the safest way. Similar names can mislead students badly."

    if student_round == "Round 2":
        return "👀 Sneaky counselling truth: For Round 2, cutoff alone is not enough. Vacancy after Round 1 decides real availability."

    if preferred_branch.upper() in ["CS", "CSE"] and branch_mode == "related":
        return "🧸 Since you chose related mode, I checked CSE family branches like IT, AIDS, AIML, Cyber Security and CSBS too."

    if preferred_branch.upper() in ["CS", "CSE"] and branch_mode == "exact":
        return "✨ Exact mode is on, so I checked only CSE. Nice when you are very sure about your branch."

    return "🌸 Pookie tip: A famous college name alone is not enough. Check cutoff, branch, vacancy and your category."


def college_card(item, category):
    priority_badge = '<span class="badge priority">⭐ Priority College</span>' if item["priority"] else ""
    vacancy_value = "No vacancy data" if item["vacancy_after_round1"] is None else str(item["vacancy_after_round1"])

    return f"""
    <div class="college-card">
        <span class="badge close">Gap: {item["close_gap"]}</span>
        <span class="badge vacancy">Round 1 vacancy: {vacancy_value}</span>
        {priority_badge}
        <br>
        <strong>{item["final_label"]}</strong><br>
        <b>{item["college_code"]} - {item["college_name"]}</b><br>
        Branch: <b>{item["branch_name"]}</b> ({item["branch_code"]})<br>
        <span class="small">
            District: {item["district"] if item["district"] else "-"} |
            Category: {category} |
            2025 cutoff: {format_number(item["cutoff"])} |
            Your difference: {format_number(item["difference"])}
            <br>
            {item["sneaky_note"]}
        </span>
    </div>
    """


@app.context_processor
def inject_helpers():
    return dict(college_card=college_card)


HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>TNEA Smart Guide</title>
    <style>
        * { box-sizing: border-box; }

        body {
            margin: 0;
            font-family: 'Segoe UI', Arial, sans-serif;
            min-height: 100vh;
            color: #2d2d2d;
            transition: 0.4s ease;
        }

        body.theme-neutral {
            background: radial-gradient(circle at top left, rgba(255,255,255,0.8), transparent 35%),
                        linear-gradient(135deg, #f8cdda, #d8b4fe, #bfdbfe);
        }

        body.theme-female {
            background: radial-gradient(circle at top left, rgba(255,255,255,0.85), transparent 35%),
                        linear-gradient(135deg, #ffe4ef, #f3d4ff, #fbcfe8);
        }

        body.theme-male {
            background: radial-gradient(circle at top left, rgba(255,255,255,0.75), transparent 35%),
                        linear-gradient(135deg, #dbeafe, #bfdbfe, #c7d2fe);
        }

        .page {
            width: 100%;
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: flex-start;
            padding: 30px 15px;
        }

        .card {
            width: 100%;
            max-width: 1120px;
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(18px);
            border-radius: 30px;
            padding: 30px;
            box-shadow: 0 20px 45px rgba(80, 60, 120, 0.22);
            animation: floatIn 0.8s ease;
        }

        @keyframes floatIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        h1 {
            text-align: center;
            color: #6d28d9;
            margin-bottom: 5px;
        }

        .subtitle {
            text-align: center;
            color: #555;
            margin-bottom: 25px;
        }

        .hero {
            background: linear-gradient(135deg, #fff1f2, #f5f3ff);
            border-radius: 24px;
            padding: 18px;
            margin-bottom: 20px;
            text-align: center;
            border: 1px solid #f0d9ff;
            line-height: 1.6;
        }

        .hero strong { color: #7e22ce; }

        .grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 15px;
        }

        label {
            font-weight: 700;
            font-size: 14px;
            color: #4b3869;
        }

        input, select {
            width: 100%;
            padding: 12px;
            margin-top: 6px;
            border: 1px solid #ddd;
            border-radius: 14px;
            font-size: 15px;
            outline: none;
            background: white;
        }

        input:focus, select:focus {
            border-color: #a855f7;
            box-shadow: 0 0 0 3px rgba(168, 85, 247, 0.15);
        }

        .full { grid-column: span 2; }

        .quick-buttons {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-top: 8px;
        }

        .quick-buttons button {
            width: auto;
            margin: 0;
            padding: 8px 12px;
            font-size: 13px;
            border-radius: 999px;
            background: #f3e8ff;
            color: #6d28d9;
            border: 1px solid #d8b4fe;
            cursor: pointer;
        }

        .main-btn {
            margin-top: 20px;
            width: 100%;
            padding: 14px;
            border: none;
            border-radius: 18px;
            background: linear-gradient(135deg, #9333ea, #ec4899);
            color: white;
            font-size: 16px;
            font-weight: bold;
            cursor: pointer;
            transition: 0.25s;
        }

        .main-btn:hover {
            transform: scale(1.02);
            box-shadow: 0 10px 20px rgba(147, 51, 234, 0.3);
        }

        .helper {
            margin-top: 10px;
            padding: 12px;
            background: #fdf2f8;
            color: #831843;
            border-radius: 16px;
            font-size: 14px;
            line-height: 1.5;
        }

        .result-box {
            margin-top: 25px;
            background: white;
            border-radius: 24px;
            padding: 22px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.08);
        }

        .cutoff {
            font-size: 28px;
            color: #7e22ce;
            font-weight: bold;
            text-align: center;
            margin-bottom: 8px;
        }

        .round {
            text-align: center;
            font-size: 20px;
            color: #be185d;
            font-weight: bold;
        }

        .message {
            background: #faf5ff;
            border-left: 6px solid #a855f7;
            border-radius: 16px;
            padding: 14px;
            margin-top: 14px;
            line-height: 1.6;
        }

        .section-title {
            margin-top: 25px;
            color: #6d28d9;
            border-bottom: 2px solid #eee;
            padding-bottom: 8px;
        }

        .count {
            font-size: 14px;
            color: #6b21a8;
            background: #f3e8ff;
            padding: 8px 12px;
            border-radius: 14px;
            display: inline-block;
            margin-top: 6px;
            margin-bottom: 8px;
        }

        .college-card {
            background: #faf5ff;
            border-left: 6px solid #a855f7;
            border-radius: 16px;
            padding: 14px;
            margin: 12px 0;
            transition: 0.2s ease;
        }

        .college-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 18px rgba(168, 85, 247, 0.16);
        }

        .college-card strong { color: #4c1d95; }

        .badge {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 999px;
            font-size: 12px;
            font-weight: bold;
            margin: 0 5px 6px 0;
        }

        .priority { background: #fde68a; color: #92400e; }
        .close { background: #dcfce7; color: #166534; }
        .vacancy { background: #dbeafe; color: #1e40af; }

        .small {
            font-size: 13px;
            color: #555;
            line-height: 1.6;
        }

        .note {
            background: #fff7ed;
            color: #7c2d12;
            padding: 12px;
            border-radius: 14px;
            margin-top: 18px;
            font-size: 14px;
            line-height: 1.6;
        }

        .error {
            background: #fee2e2;
            color: #991b1b;
            padding: 12px;
            border-radius: 14px;
            margin-top: 18px;
            font-weight: bold;
        }

        .empty {
            text-align: center;
            color: #666;
            padding: 15px;
            background: #f9fafb;
            border-radius: 14px;
            margin-top: 10px;
        }

        .choice-helper {
            background: #ecfeff;
            color: #155e75;
            border-left: 6px solid #06b6d4;
            border-radius: 16px;
            padding: 14px;
            margin-top: 20px;
            line-height: 1.6;
        }

        @media (max-width: 650px) {
            .grid { grid-template-columns: 1fr; }
            .full { grid-column: span 1; }
            .card { padding: 22px; }
        }
    </style>
</head>

<body class="{{ theme_class }}">
<div class="page">
<div class="card">

    <h1>🎓 TNEA Smart Guide</h1>
    <p class="subtitle">Cutoff + vacancy reality checker, but make it pookie 🌸</p>

    <div class="hero">
        <strong>🧸 Smart counselling rule:</strong><br>
        Cutoff shows what looked possible. Vacancy shows what was actually available in that round.
    </div>

    {% if file_error %}
        <div class="error">
            CSV file not found. Keep <b>tnea_2025_cutoff_vs_round1_vacancy_clean_no_2020_2021.csv</b> in the same folder as app.py.
        </div>
    {% endif %}

    <form method="POST">
        <div class="grid">

            <div>
                <label>Name *</label>
                <input type="text" name="name" placeholder="Enter your name" required>
            </div>

            <div>
                <label>Gender optional</label>
                <select name="gender" id="genderSelect" onchange="previewTheme()">
                    <option value="">Prefer not to say</option>
                    <option value="Female">Female</option>
                    <option value="Male">Male</option>
                    <option value="Other">Other</option>
                </select>
            </div>

            <div>
                <label>Date of Birth optional</label>
                <input type="date" name="dob">
            </div>

            <div>
                <label>Board *</label>
                <select name="board" required>
                    <option value="">Select board</option>
                    <option value="State Board">State Board</option>
                    <option value="CBSE">CBSE</option>
                    <option value="ICSE">ICSE</option>
                    <option value="Other">Other</option>
                </select>
            </div>

            <div>
                <label>Physics Mark out of 100 *</label>
                <input type="number" step="0.01" name="physics" min="0" max="100" required>
            </div>

            <div>
                <label>Chemistry Mark out of 100 *</label>
                <input type="number" step="0.01" name="chemistry" min="0" max="100" required>
            </div>

            <div>
                <label>Maths Mark out of 100 *</label>
                <input type="number" step="0.01" name="maths" min="0" max="100" required>
            </div>

            <div>
                <label>Category *</label>
                <select name="category" required>
                    <option value="">Select category</option>
                    <option value="OC">OC</option>
                    <option value="BC">BC</option>
                    <option value="BCM">BCM</option>
                    <option value="MBC">MBC</option>
                    <option value="SC">SC</option>
                    <option value="SCA">SCA</option>
                    <option value="ST">ST</option>
                </select>
            </div>

            <div class="full">
                <label>Choose Mode *</label>
                <select name="mode" id="modeSelect" required onchange="updateModeHelp()">
                    <option value="">Select mode</option>
                    <option value="options">Explore My Options</option>
                    <option value="dream">Check Dream College by College Code</option>
                </select>

                <div class="helper" id="modeHelp">
                    🌸 Explore shows realistic options. Dream checks one college code safely.
                </div>
            </div>

            <div>
                <label>Preferred Branch optional</label>
                <input type="text" id="branchInput" name="preferred_branch" placeholder="CS, ECE, IT, AD or leave empty">

                <div class="quick-buttons">
                    <button type="button" onclick="setBranch('CS')">CS</button>
                    <button type="button" onclick="setBranch('EC')">ECE</button>
                    <button type="button" onclick="setBranch('IT')">IT</button>
                    <button type="button" onclick="setBranch('AD')">AIDS</button>
                    <button type="button" onclick="setBranch('ANY')">All branches</button>
                </div>
            </div>

            <div>
                <label>Branch Search Mode</label>
                <select name="branch_mode">
                    <option value="related">Related branch family</option>
                    <option value="exact">Exact branch only</option>
                </select>
            </div>

            <div>
                <label>District Filter optional</label>
                <select name="district_filter">
                    <option value="ANY">Any district</option>
                    {% for d in districts %}
                        <option value="{{ d }}">{{ d }}</option>
                    {% endfor %}
                </select>
            </div>

            <div>
                <label>College Code for Dream College only</label>
                <input type="text" name="college_code" placeholder="Example: 1211, 1422, 2006">
            </div>

        </div>

        <button class="main-btn" type="submit">Unlock My Realistic TNEA List 🔓</button>
    </form>

    {% if error %}
        <div class="error">{{ error }}</div>
    {% endif %}

    {% if submitted %}
    <div class="result-box">

        <p class="cutoff">{{ name }}, your cutoff is {{ cutoff }}</p>
        <p class="round">Expected counselling: {{ round_name }}</p>

        <div class="message">{{ round_message }}</div>

        {% for msg in praise_messages %}
            <div class="message">{{ msg }}</div>
        {% endfor %}

        <div class="message">{{ pookie_message }}</div>

        <div class="note">
            Search mode: <b>{{ branch_mode_label }}</b> |
            District filter: <b>{{ district_filter }}</b><br>
            This app uses 2025 cutoff data + 2025 vacancy after Round 1. For Round 2 students, vacancy after Round 1 is used as the reality checker.
        </div>

        {% if mode == "options" %}

            <h2 class="section-title">✨ Realistic Safe Options</h2>
            <span class="count">{{ safe_count }} found. Showing best {{ safe_showing }}.</span>
            {% if safe %}
                {% for item in safe[:60] %}
                    {{ college_card(item, category)|safe }}
                {% endfor %}
            {% else %}
                <div class="empty">No realistic safe options found for this search.</div>
            {% endif %}

            <h2 class="section-title">🌷 Successor / Good Try Options</h2>
            <span class="count">{{ successor_count }} found. Showing best {{ successor_showing }}.</span>
            {% if successor %}
                {% for item in successor[:60] %}
                    {{ college_card(item, category)|safe }}
                {% endfor %}
            {% else %}
                <div class="empty">No successor options found for this search.</div>
            {% endif %}

            <h2 class="section-title">⚠️ Risky Despite Cutoff</h2>
            <span class="count">{{ risky_count }} found. Showing best {{ risky_showing }}.</span>
            {% if risky %}
                {% for item in risky[:60] %}
                    {{ college_card(item, category)|safe }}
                {% endfor %}
            {% else %}
                <div class="empty">No risky cutoff-vacancy mismatch found.</div>
            {% endif %}

            <h2 class="section-title">🎯 Dream Options</h2>
            <span class="count">{{ dream_count }} found. Showing best {{ dream_showing }}.</span>
            {% if dream %}
                {% for item in dream[:60] %}
                    {{ college_card(item, category)|safe }}
                {% endfor %}
            {% else %}
                <div class="empty">No dream options found.</div>
            {% endif %}

            <div class="choice-helper">
                🧸 <b>Choice filling helper:</b><br>
                Put real dream choices first, then good tries, then realistic safe backups. But don’t trust a college only because cutoff looks possible — vacancy decides the round reality.
            </div>

        {% elif mode == "dream" %}

            <h2 class="section-title">🎯 Dream College Reality Check</h2>
            <span class="count">{{ dream_result_count }} branch results found for this college code.</span>

            <div class="choice-helper">
                🎯 <b>College code safety note:</b><br>
                This mode uses college code because similar college names can mislead students. Verify the code again before final choice filling.
            </div>

            {% if dream_results %}
                {% for item in dream_results %}
                    {{ college_card(item, category)|safe }}
                {% endfor %}
            {% else %}
                <div class="empty">
                    No matching college code found, or no data available for this category.
                </div>
            {% endif %}

        {% endif %}

    </div>
    {% endif %}

</div>
</div>

<script>
function setBranch(value) {
    document.getElementById("branchInput").value = value;
}

function updateModeHelp() {
    const mode = document.getElementById("modeSelect").value;
    const help = document.getElementById("modeHelp");

    if (mode === "options") {
        help.innerHTML = "✨ Explore mode: branch is optional. Leave empty to see all branches, or type CS/ECE/IT/AD.";
    } else if (mode === "dream") {
        help.innerHTML = "🎯 Dream mode: college code is compulsory. This avoids same-name confusion.";
    } else {
        help.innerHTML = "🌸 Explore shows realistic options. Dream checks one college code safely.";
    }
}

function previewTheme() {
    const gender = document.getElementById("genderSelect").value;
    document.body.classList.remove("theme-female", "theme-male", "theme-neutral");

    if (gender === "Female") {
        document.body.classList.add("theme-female");
    } else if (gender === "Male") {
        document.body.classList.add("theme-male");
    } else {
        document.body.classList.add("theme-neutral");
    }
}
</script>

</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
def home():
    data = load_master_data()
    file_error = len(data) == 0
    districts = get_districts(data)

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        gender = request.form.get("gender", "").strip()
        board = request.form.get("board", "").strip()
        category = request.form.get("category", "").strip()
        mode = request.form.get("mode", "").strip()
        preferred_branch = request.form.get("preferred_branch", "").strip().upper()
        college_code = request.form.get("college_code", "").strip()
        district_filter = request.form.get("district_filter", "ANY").strip()
        branch_mode = request.form.get("branch_mode", "related").strip()

        error = None

        if not name or not board or not category or not mode:
            error = "Please fill all required fields."

        if mode == "options" and not preferred_branch:
            preferred_branch = "ANY"

        if mode == "dream" and not college_code:
            error = "Please enter college code for Dream College mode."

        try:
            physics = float(request.form.get("physics", ""))
            chemistry = float(request.form.get("chemistry", ""))
            maths = float(request.form.get("maths", ""))
        except ValueError:
            physics = chemistry = maths = 0
            error = "Please enter valid marks."

        if not error:
            cutoff = calculate_cutoff(physics, chemistry, maths)
            round_name, round_message = predict_round(cutoff)
            praise_messages = subject_praise(maths, physics, chemistry)
            pookie_message = pookie_tip(mode, preferred_branch, round_name, branch_mode)

            safe, successor, risky, dream = [], [], [], []
            dream_results = []

            if mode == "options":
                safe, successor, risky, dream = explore_options(
                    data,
                    cutoff,
                    category,
                    preferred_branch,
                    round_name,
                    district_filter,
                    branch_mode
                )
                mode_label = "Explore My Options"
            else:
                dream_results = dream_college_check(data, cutoff, category, college_code, round_name)
                mode_label = "Check Dream College"

            branch_mode_label = "Exact branch only" if branch_mode == "exact" else "Related branch family"

            return render_template_string(
                HTML,
                file_error=file_error,
                submitted=True,
                error=None,
                name=name,
                board=board,
                category=category,
                mode=mode,
                mode_label=mode_label,
                cutoff=format_number(cutoff),
                round_name=round_name,
                round_message=round_message,
                praise_messages=praise_messages,
                pookie_message=pookie_message,
                safe=safe,
                successor=successor,
                risky=risky,
                dream=dream,
                dream_results=dream_results,
                safe_count=len(safe),
                successor_count=len(successor),
                risky_count=len(risky),
                dream_count=len(dream),
                safe_showing=min(len(safe), 60),
                successor_showing=min(len(successor), 60),
                risky_showing=min(len(risky), 60),
                dream_showing=min(len(dream), 60),
                dream_result_count=len(dream_results),
                theme_class=gender_theme(gender),
                districts=districts,
                district_filter=district_filter if district_filter != "ANY" else "Any district",
                branch_mode_label=branch_mode_label
            )

        return render_template_string(
            HTML,
            file_error=file_error,
            submitted=False,
            error=error,
            theme_class="theme-neutral",
            districts=districts
        )

    return render_template_string(
        HTML,
        file_error=file_error,
        submitted=False,
        error=None,
        theme_class="theme-neutral",
        districts=districts
    )


if __name__ == "__main__":
    app.run(debug=True)