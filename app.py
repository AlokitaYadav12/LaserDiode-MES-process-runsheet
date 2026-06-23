import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime
from fpdf import FPDF
import plotly.express as px

# -------------------------
# PAGE CONFIG
# -------------------------
st.set_page_config(
    page_title="Laser Diode MES",
    layout="wide"
)

# -------------------------
# CUSTOM CSS
# -------------------------

st.markdown("""
<style>

.stApp{
    background: linear-gradient(
    135deg,
    #EEF4FF,
    #DDEAF7,
    #F8FAFC
    );
}

[data-testid="stSidebar"]{
    background:#0F172A;
}

[data-testid="stSidebar"] *{
    color:white;
}

h1,h2,h3{
    color:#003366;
    font-weight:bold;
}

[data-testid="stMetricValue"]{
    font-size:30px;
    font-weight:bold;
}

.stDataFrame{
    border-radius:10px;
}

</style>
""", unsafe_allow_html=True)
st.markdown("""
<style>

div.stButton > button{

background:#2563eb;
color:white;
border-radius:10px;
border:none;

}

div.stButton > button:hover{

background:#1d4ed8;
color:white;

}

</style>
""",unsafe_allow_html=True)

# -------------------------
# DATABASE
# -------------------------
conn = sqlite3.connect(
    "laser_mes.db",
    check_same_thread=False
)

cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS users(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    email TEXT UNIQUE,
    login_time TEXT
)
""")
conn.commit()


# WAFER TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS wafers(
wafer_id TEXT PRIMARY KEY,
material TEXT,
diameter REAL,
batch_no TEXT,
created_at TEXT
)
""")

# PROCESS TABLE
cursor.execute("""
CREATE TABLE IF NOT EXISTS process_runs(
id INTEGER PRIMARY KEY AUTOINCREMENT,
wafer_id TEXT,
process_name TEXT,
operator_name TEXT,
parameters TEXT,
remarks TEXT,
timestamp TEXT
)
""")

conn.commit()

cursor.execute("""
CREATE TABLE IF NOT EXISTS inspections(

id INTEGER PRIMARY KEY AUTOINCREMENT,

wafer_id TEXT,

process_name TEXT,

inspection_point TEXT,

geometry_check TEXT,

status TEXT,

remarks TEXT,

timestamp TEXT

)
""")

conn.commit()

# -------------------------
# AI PROCESS INSPECTION
# -------------------------

def ai_inspection(process, params):

    status = "PASS"
    message = "All parameters are within specification."
    hint = "No action required."

    # -----------------------------
    # CLEANING
    # -----------------------------
    if process == "Cleaning":

        acetone = params["acetone"]
        ipa = params["ipa"]

        if acetone < 3 or acetone > 10:
            status = "ERROR"
            message = "Acetone cleaning time is outside specification."
            hint = "Allowed Range : 3 - 10 min"

        elif acetone < 4 or acetone > 8:
            status = "WARNING"
            message = "Acetone cleaning time is near the limit."
            hint = "Ideal Range : 4 - 8 min"

        if ipa < 2 or ipa > 8:
            status = "ERROR"
            message = "IPA cleaning time is outside specification."
            hint = "Allowed Range : 2 - 8 min"

        elif ipa < 3 or ipa > 6:
            status = "WARNING"
            message = "IPA cleaning time is near the limit."
            hint = "Ideal Range : 3 - 6 min"

    # -----------------------------
    # PHOTOLITHOGRAPHY
    # -----------------------------
    elif process == "Photolithography":

        spin = params["spin"]
        bake = params["bake"]

        if spin < 2500 or spin > 5000:
            status = "ERROR"
            message = "Spin speed outside specification."
            hint = "Allowed Range : 2500 - 5000 rpm"

        elif spin < 3000 or spin > 4500:
            status = "WARNING"
            message = "Spin speed near limit."
            hint = "Ideal Range : 3000 - 4500 rpm"

        if bake < 80 or bake > 120:
            status = "ERROR"
            message = "Bake temperature outside specification."
            hint = "Allowed Range : 80 - 120 °C"

        elif bake < 90 or bake > 110:
            status = "WARNING"
            message = "Bake temperature near limit."
            hint = "Ideal Range : 90 - 110 °C"

    # -----------------------------
    # ETCHING
    # -----------------------------
    elif process == "Etching":

        etch = params["etch"]

        if etch < 30 or etch > 300:
            status = "ERROR"
            message = "Etching time outside specification."
            hint = "Allowed Range : 30 - 300 sec"

        elif etch < 60 or etch > 240:
            status = "WARNING"
            message = "Etching time near limit."
            hint = "Ideal Range : 60 - 240 sec"

    # -----------------------------
    # METALLIZATION
    # -----------------------------
    elif process == "Metallization":

        thickness = params["thickness"]

        if thickness < 100 or thickness > 500:
            status = "ERROR"
            message = "Metal thickness outside specification."
            hint = "Allowed Range : 100 - 500 nm"

        elif thickness < 150 or thickness > 400:
            status = "WARNING"
            message = "Metal thickness near limit."
            hint = "Ideal Range : 150 - 400 nm"

    # -----------------------------
    # ANNEALING
    # -----------------------------
    elif process == "Annealing":

        temp = params["temp"]
        duration = params["duration"]

        if temp < 350 or temp > 450:
            status = "ERROR"
            message = "Annealing temperature outside specification."
            hint = "Allowed Range : 350 - 450 °C"

        elif temp < 380 or temp > 430:
            status = "WARNING"
            message = "Annealing temperature near limit."
            hint = "Ideal Range : 380 - 430 °C"

        if duration < 20 or duration > 90:
            status = "ERROR"
            message = "Annealing duration outside specification."
            hint = "Allowed Range : 20 - 90 min"

    # -----------------------------
    # CLEAVING
    # -----------------------------


    elif process=="Cleaving":

        angle = params["angle"]

        if angle < 85 or angle > 95:
            status="ERROR"
            message="Cleaving angle outside specification."
            hint="Allowed range: 85-95 degree"

    # -----------------------------
    # FACET COATING
    # -----------------------------
    elif process=="Facet Coating":

        thickness = params["thickness"]

        if thickness < 100 or thickness > 300:
            status="ERROR"
            message="Facet coating thickness outside specification."
            hint="Allowed range: 100-300 nm"

    # -----------------------------
    # WIRE BONDING
    # -----------------------------
    elif process=="Wire Bonding":

        strength = params["strength"]

        if strength < 5:
            status="WARNING"
            message="Low wire bond strength."
            hint="Check bonding parameters"


    # -----------------------------
    # TESTING
    # -----------------------------
    elif process == "Testing":

        current = params["current"]
        power = params["power"]
        wavelength = params["wavelength"]

        if current < 20 or current > 80:
            status = "ERROR"
            message = "Threshold current outside specification."
            hint = "Allowed Range : 20 - 80 mA"

        elif current < 30 or current > 60:
            status = "WARNING"
            message = "Threshold current near limit."
            hint = "Ideal Range : 30 - 60 mA"

        if power < 5 or power > 50:
            status = "ERROR"
            message = "Output power outside specification."
            hint = "Allowed Range : 5 - 50 mW"

        elif power < 10 or power > 30:
            status = "WARNING"
            message = "Output power near limit."
            hint = "Ideal Range : 10 - 30 mW"

        if wavelength < 900 or wavelength > 1100:
            status = "ERROR"
            message = "Wavelength outside specification."
            hint = "Allowed Range : 900 - 1100 nm"

        elif wavelength < 940 or wavelength > 1060:
            status = "WARNING"
            message = "Wavelength near limit."
            hint = "Ideal Range : 940 - 1060 nm"

    return status, message, hint

# -------------------------
# LOGIN
# -------------------------
# -----------------------------
# LOGIN PAGE
# -----------------------------

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

if not st.session_state.logged_in:

    st.markdown("""
    <style>

    .loginbox{

    max-width:600px;
    margin:auto;
    margin-top:80px;

    padding:45px;

    border-radius:25px;

    background:
    linear-gradient(
    135deg,
    #020617,
    #1E3A8A,
    #0369A1
    );

    text-align:center;

    box-shadow:
    0px 15px 50px rgba(0,0,0,0.5);

    }


    .loginbox h1{

    color:white;

    font-size:48px;

    font-weight:900;

    letter-spacing:2px;

    }


    .loginbox h3{

    color:#BAE6FD;

    font-size:25px;

    }


    .loginbox p{

    color:white;

    font-size:20px;

    }


    </style>
    """,unsafe_allow_html=True)



    st.markdown("""
    <div class="loginbox">

    <h1>
    🔬 LASER DIODE MES
    </h1>

    <h3>
    Manufacturing Execution System
    </h3>

    <p>
    AI Based Fabrication Monitoring & Inspection
    </p>

    <p>
    🔐 Please Login
    </p>


    </div>

    """,unsafe_allow_html=True)
    name = st.text_input("👤 Full Name")

    email = st.text_input("📧 Email Address")

    if st.button("Login"):

        if name != "" and email != "":

            cursor.execute(
                "SELECT * FROM users WHERE email=?",
                (email,)
            )

            user = cursor.fetchone()

            if user is None:

                cursor.execute(
                    """
                    INSERT INTO users
                    (name,email,login_time)
                    VALUES(?,?,?)
                    """,
                    (
                        name,
                        email,
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                    )
                )

                conn.commit()

            st.session_state.logged_in = True
            st.session_state.user = name
            st.session_state.email = email

            st.rerun()

        else:
            st.error("Please enter Name and Email.")

    st.stop()
# -------------------------
def generate_pdf(selected_wafer=None):

    pdf = FPDF()

    pdf.add_page()


    # -------------------------
    # HEADER
    # -------------------------

    pdf.set_fill_color(15,23,42)

    pdf.rect(
        0,
        0,
        210,
        30,
        "F"
    )


    pdf.set_text_color(
        255,
        255,
        255
    )

    pdf.set_font(
        "Arial",
        "B",
        18
    )


    pdf.cell(
        190,
        15,
        "LASER DIODE FABRICATION REPORT",
        align="C"
    )


    pdf.ln(20)


    # -------------------------
    # BASIC INFO
    # -------------------------

    pdf.set_text_color(
        0,
        0,
        0
    )

    pdf.set_font(
        "Arial",
        "",
        12
    )


    pdf.cell(
        190,
        10,
        f"Generated Date: {datetime.now()}",
        ln=True
    )


    pdf.cell(
        190,
        10,
        "Manufacturing Execution System",
        ln=True
    )


    pdf.ln(10)



    # -------------------------
    # WAFER DATA
    # -------------------------

    pdf.set_font(
        "Arial",
        "B",
        14
    )


    pdf.cell(
        190,
        10,
        "Wafer Registration Details",
        ln=True
    )


    pdf.set_font(
        "Arial",
        "",
        10
    )


    if selected_wafer:

        wafer_data = pd.read_sql(
              """
              SELECT * FROM wafers
              WHERE wafer_id=?
              """,
              conn,
              params=(selected_wafer,)
        )

    else:

        wafer_data = pd.read_sql(
              "SELECT * FROM wafers",
               conn
        )

    for index,row in wafer_data.iterrows():

        pdf.cell(
            190,
            8,
            f"Wafer ID: {row['wafer_id']} | Material: {row['material']} | Batch: {row['batch_no']}",
            ln=True
        )



    pdf.ln(10)



    # -------------------------
    # PROCESS DATA
    # -------------------------

    pdf.set_font(
        "Arial",
        "B",
        14
    )


    pdf.cell(
        190,
        10,
        "Fabrication Process History",
        ln=True
    )


    pdf.set_font(
        "Arial",
        "",
        9
    )


    if selected_wafer:

        process_data = pd.read_sql(
              """
              SELECT * FROM process_runs
              WHERE wafer_id=?
              """,
              conn,
              params=(selected_wafer,)
        )

    else:

         process_data = pd.read_sql(
             "SELECT * FROM process_runs",
             conn
         )

    for index,row in process_data.iterrows():

        pdf.multi_cell(
            190,
            7,
            f"""
Process: {row['process_name']}
Wafer: {row['wafer_id']}
Operator: {row['operator_name']}
Parameters: {row['parameters']}
Remarks: {row['remarks']}
Time: {row['timestamp']}

-----------------------------
"""
        )



    filename = "Laser_Diode_Fabrication_Report.pdf"


    pdf.output(
        filename
    )


    return filename
    
# -------------------------
# SIDEBAR
# -------------------------
# SIDEBAR USER AREA

st.sidebar.markdown("---")

st.sidebar.write("👤 User")

st.sidebar.write(
st.session_state.get("user","Guest")
)


if st.sidebar.button("🚪 Logout"):

    st.session_state.logged_in=False
    st.session_state.user=""

    st.rerun()

page = st.sidebar.radio(
    "Navigation",
    [
        "Dashboard",
        "Wafer Registration",
        "Process Run Sheet",
        "View Data",
        "Reports",
        "Delete Records" 
    ]
)
process_flow = [
    "Cleaning",
    "Photolithography",
    "Etching",
    "Metallization",
    "Annealing",
    "Cleaving",
    "Facet Coating",
    "Wire Bonding",
    "Testing"
]

if "current_step" not in st.session_state:
    st.session_state.current_step = 0


if "run_saved" not in st.session_state:
    st.session_state.run_saved = False

if "fabrication_completed" not in st.session_state:
    st.session_state.fabrication_completed = False

# -------------------------
# DASHBOARD
# -------------------------
if page == "Dashboard":

    st.markdown(f"""

    <div style="
    background:linear-gradient(90deg,#001F54,#034078,#1282A2);
    padding:30px;
    border-radius:20px;
    color:white;
    text-align:center;
    ">

    <h1>
    👋 Welcome {st.session_state.get("user","Operator")}
    </h1>

    <h2>
    🔬 Laser Diode Manufacturing Execution System
    </h2>

    <p>
    Fabrication Monitoring Dashboard
    </p>

    </div>

    """,unsafe_allow_html=True)
    wafer_count = cursor.execute(
        "SELECT COUNT(*) FROM wafers"
    ).fetchone()[0]

    process_count = cursor.execute(
        "SELECT COUNT(*) FROM process_runs"
    ).fetchone()[0]

    operator_count = cursor.execute(
        "SELECT COUNT(DISTINCT operator_name) FROM process_runs"
    ).fetchone()[0]

    col1,col2,col3,col4 = st.columns(4)

    cards = [
    ("🧪 Wafers", wafer_count, "#2563EB"),
    ("⚙ Processes", process_count, "#059669"),
    ("👨‍🔬 Operators", operator_count, "#7C3AED"),   
    ("📈 Yield", "92%" if process_count > 0 else "0%", "#DC2626")
    ]

    for col,(title,val,color) in zip([col1,col2,col3,col4],cards):
         with col:
             st.markdown(f"""
             <div style="
             background:{color};
             padding:20px;
             border-radius:15px;
             text-align:center;
             color:white;">
             <h4>{title}</h4>
             <h1>{val}</h1>
             </div>
             """, unsafe_allow_html=True)
    st.info(
        f"Current Manufacturing Step: {process_flow[st.session_state.current_step]}"
    )
    st.subheader("🏭 Fabrication Workflow")

    workflow_display = []

    for i, step in enumerate(process_flow):

        if i < st.session_state.current_step:
            workflow_display.append(
                f"{step} ✅"
            )

        elif i == st.session_state.current_step:
            workflow_display.append(
                f"{step} 🔄"
            )

        else:
            workflow_display.append(
                f"{step} ⏳"
            )


    st.write(
        " → ".join(workflow_display)
    )


    progress = (
        st.session_state.current_step
        /
        (len(process_flow)-1)
    )

    st.progress(progress)
    
    chart_data = pd.read_sql("""
    SELECT process_name,
    COUNT(*) as Count
    FROM process_runs
    GROUP BY process_name
    """, conn)

    if len(chart_data)>0:
         fig = px.pie(
             chart_data,
             values="Count",
             names="process_name",
             title="Fabrication Process Distribution"
         )
         st.plotly_chart(fig, width="stretch")

    st.subheader("🔍 Wafer Search")

    search = st.text_input("Enter Wafer ID")

    if search:
         result = pd.read_sql(
             """
             SELECT *
             FROM process_runs
             WHERE wafer_id=?
             """,
             conn,
             params=(search,)
         )         
         st.dataframe(result)

    st.subheader("🖥 Equipment Status")

    equipment = [
        ("Mask Aligner", "ONLINE"),
        ("Evaporator", "ONLINE"),
        ("Annealing Furnace", "MAINTENANCE")
    ]


    col1,col2,col3 = st.columns(3)

    for col,(name,status) in zip(
        [col1,col2,col3],
        equipment
    ):

        with col:

            if status=="ONLINE":
                st.success(
                    f"{name}: {status}"
                )

            else:
                st.warning(
                    f"{name}: {status}"
                )
    st.subheader("📋 Recent Fabrication Activity")

    recent = pd.read_sql("""
    SELECT
    wafer_id,
    process_name,
    operator_name,
    parameters,
    remarks,
    timestamp
    FROM process_runs
    ORDER BY id DESC
    LIMIT 10
    """, conn)

    st.dataframe(
        recent,
        width="stretch"
    )

# -------------------------
# WAFER REGISTRATION
# -------------------------
elif page == "Wafer Registration":

    st.header("Wafer Registration")

    wafer_id = st.text_input(
        "Wafer ID"
    )

    material = st.selectbox(
        "Material",
        ["GaAs","InP","GaN"]
    )

    diameter = st.number_input(
        "Diameter (inch)"
    )

    batch_no = st.text_input(
        "Batch Number"
    )

    if st.button(
        "Register Wafer"
    ):

        try:

            cursor.execute(
                """
                INSERT INTO wafers
                VALUES(?,?,?,?,?)
                """,
                (
                    wafer_id,
                    material,
                    diameter,
                    batch_no,
                    datetime.now().strftime(
                        "%Y-%m-%d %H:%M:%S"
                    )
                )
            )

            conn.commit()

            st.success(
                "Wafer Registered"
            )

        except:
            st.error(
                "Wafer Already Exists"
            )

# -------------------------
# PROCESS RUN SHEET
# -------------------------

elif page == "Process Run Sheet":

    st.header("Process Run Sheet")

    if "current_step" not in st.session_state:
        st.session_state.current_step = 0


    if "process_box" not in st.session_state:
         st.session_state.process_box = process_flow[0]

    process = st.selectbox(
       "Current Process",
       process_flow,
       index=st.session_state.current_step
    )
      
 
    progress = (
        (st.session_state.current_step)
        /
        (len(process_flow)-1)
    )

    st.progress(progress)

    st.info(
        f"Step {st.session_state.current_step+1} / {len(process_flow)} : {process}"
    )


    wafers = pd.read_sql(
        "SELECT wafer_id FROM wafers",
        conn
    )

    if len(wafers)==0:

        st.warning(
            "Register Wafer First"
        )

    else:

        st.subheader("🧪 Wafer Selection")

        mass_mode = st.checkbox(
              "Enable Mass Wafer Processing"
        )


        if mass_mode:

              selected_wafers = st.multiselect(
                  "Select Multiple Wafers",
                  wafers["wafer_id"]
              )

        else:

              selected_wafers = [
                  st.selectbox(
                     "Select Wafer",
                     wafers["wafer_id"],
                     key="single_wafer"
                  )
              ]

        operator = st.text_input(
            "Operator Name"
        )

        params = ""

        # CLEANING
        if process=="Cleaning":

            acetone = st.number_input(
                "Acetone Time (min)"
            )

            ipa = st.number_input(
                "IPA Time (min)"
            )

            params = f"Acetone={acetone}, IPA={ipa}"

        # PHOTOLITHOGRAPHY
        elif process=="Photolithography":

            resist = st.text_input(
                "Photoresist"
            )

            spin = st.number_input(
                "Spin Speed (rpm)"
            )

            bake = st.number_input(
                "Bake Temp (°C)"
            )

            params = f"Resist={resist}, Spin={spin}, Bake={bake}"

        # ETCHING
        elif process=="Etching":

            etch_time = st.number_input(
                "Etch Time"
            )

            chemical = st.text_input(
                "Chemical"
            )

            params = f"Etch={etch_time}, Chemical={chemical}"

        # METALLIZATION
        elif process=="Metallization":

            metal = st.text_input(
                "Metal Stack"
            )

            thickness = st.number_input(
                "Thickness (nm)"
            )

            params = f"Metal={metal}, Thickness={thickness}"

        # ANNEALING
        elif process=="Annealing":

            temp = st.number_input(
                "Temperature (°C)"
            )

            duration = st.number_input(
                "Duration (min)"
            )

            if temp > 450:
                st.warning(
                    "Temperature above SOP"
                )

            params = f"Temp={temp}, Duration={duration}"
        
        # CLEAVING

        elif process=="Cleaving":

            cleave_angle = st.number_input(
                "Cleaving Angle (degree)"
            )

            edge_quality = st.selectbox(
                "Edge Quality",
                [
                    "Good",
                    "Average",
                    "Poor"
                ]
            )

            params = (
                f"Angle={cleave_angle}, "
                f"Edge Quality={edge_quality}"
            )



        # FACET COATING

        elif process=="Facet Coating":

            coating = st.text_input(
                "Coating Material"
            )

            thickness = st.number_input(
                "Coating Thickness (nm)"
            )

            uniformity = st.selectbox(
                "Coating Uniformity",
                [
                    "Pass",
                    "Fail"
                ]
            )

            params = (
                f"Material={coating}, "
                f"Thickness={thickness}, "
                f"Uniformity={uniformity}"
            )



        # WIRE BONDING

        elif process=="Wire Bonding":

            wire_material = st.text_input(
                "Wire Material"
            )

            bond_temp = st.number_input(
                "Bond Temperature (°C)"
            )

            pull_strength = st.number_input(
                "Pull Strength (g)"
            )

            params = (
                f"Wire={wire_material}, "
                f"Temperature={bond_temp}, "
                f"Strength={pull_strength}"
            )




        # TESTING
        elif process=="Testing":

            current = st.number_input(
                "Threshold Current (mA)"
            )

            power = st.number_input(
                "Output Power (mW)"
            )

            wavelength = st.number_input(
                "Wavelength (nm)"
            )

            params = f"Current={current}, Power={power}, Wavelength={wavelength}"

        remarks = st.text_area(
            "Remarks"
        )

        if st.button("Inspect & Save Run Sheet", key="inspect_save"):

           inspection_data = {}

           if process=="Cleaning":
               inspection_data={
                  "acetone":acetone,
                  "ipa":ipa
               }

           elif process=="Photolithography":
               inspection_data={
                  "spin":spin,
                  "bake":bake
               }

           elif process=="Etching":
               inspection_data={
                  "etch":etch_time
               }

           elif process=="Metallization":
               inspection_data={
                  "thickness":thickness
               }

           elif process=="Annealing":
               inspection_data={
                  "temp":temp,
                  "duration":duration
               }

           elif process=="Cleaving":
               inspection_data={
                  "angle":cleave_angle
           }


           elif process=="Facet Coating":
               inspection_data={
                  "thickness":thickness
           }


           elif process=="Wire Bonding":
               inspection_data={
                  "strength":pull_strength
           }

           elif process=="Testing":
              inspection_data={
                  "current":current,
                  "power":power,
                  "wavelength":wavelength
               }


           status, message, hint = ai_inspection(
           process,
           inspection_data
           )
           
           st.subheader("🔍 Automatic Process Inspection Points")

           inspection_database = {

           "Cleaning":[
           "Surface contamination check",
           "Residue removal verification",
           "Particle inspection",
           "Cleaning uniformity"
           ],

           "Photolithography":[
           "Resist thickness verification",
           "Pattern alignment check",
           "Exposure quality"
           ],

           "Etching":[
           "Etch depth verification",
           "Sidewall profile check",
           "Surface damage inspection"
           ],

           "Metallization":[
           "Metal thickness check",
           "Adhesion verification",
           "Layer uniformity"
           ],

           "Annealing":[
           "Temperature profile check",
           "Material activation",
           "Surface condition"
           ],

           "Cleaving":[
           "Cleave angle verification",
           "Facet quality inspection",
           "Edge damage inspection"
           ],

           "Facet Coating":[
           "Coating thickness verification",
           "Facet reflectivity check",
           "Uniform coating inspection"
           ],


           "Wire Bonding":[
           "Bond strength verification",
           "Wire alignment check",
           "Electrical connection inspection"
           ],

           "Testing":[
           "Current verification",
           "Optical power check",
           "Wavelength accuracy"
           ]

           }


           for point in inspection_database[process]:
               st.success("✓ " + point)

           st.subheader("📐 Automatic Geometry Consideration")


           geometry_database = {

           "Cleaning":
           "Wafer surface flatness and scratch inspection",

           "Photolithography":
           "Line width and resist thickness verification",

           "Etching":
           "Etch depth and sidewall angle verification",

           "Metallization":
           "Film thickness and contact dimension check",

           "Annealing":
           "Surface morphology and thermal stability",
           
           "Cleaving":
           "Facet angle and chip dimension verification",

           "Facet Coating":
           "Facet surface and coating thickness verification",

           "Wire Bonding":
           "Bond position and wire geometry verification",

           "Testing":
           "Emission profile and device geometry"

           }


           st.info(
           geometry_database[process]
           )    

           
           if status == "PASS":

               st.success("✅ AI Inspection Passed")
               st.info("All parameters are within the ideal operating range.")

           elif status == "WARNING":

               st.warning("⚠️ " + message)
               st.info("💡 " + hint)

           elif status == "ERROR":

               st.error("❌ " + message)
               st.error("Recommended: " + hint)
               st.stop()

           
           for wafer_id in selected_wafers:

               cursor.execute(
               """
               INSERT INTO process_runs
               (
                   wafer_id,
                   process_name,
                   operator_name,
                   parameters,
                   remarks,
                   timestamp
               )
               VALUES(?,?,?,?,?,?)
               """,
               (
                   wafer_id,
                   process,
                   operator,
                   params,
                   remarks,
                   datetime.now().strftime("%Y-%m-%d %H:%M:%S")
               )
               )

           conn.commit()
           
           cursor.execute(
           """
           INSERT INTO inspections
           (
           wafer_id,
           process_name,
           inspection_point,
           geometry_check,
           status,
           remarks,
           timestamp
           )
           VALUES(?,?,?,?,?,?,?)
           """,
           (
           selected_wafers[0],
           process,
           "Automatic AI Inspection",
           geometry_database[process],
           status,
           remarks,
           datetime.now().strftime("%Y-%m-%d %H:%M:%S")
           )
           )

           conn.commit()
           
           st.success("Run Sheet Saved")
           st.session_state.run_saved = True

        if st.session_state.run_saved:

           if st.button(
            "➡️ Next Process",
            key="next_process"
           ):

               if st.session_state.current_step < len(process_flow)-1:

                  st.session_state.current_step += 1

                  st.session_state.run_saved = False
                  
                 

                  st.rerun()

               else:

                  st.session_state.fabrication_completed = True
                  st.success(
                      "🎉 Fabrication Flow Completed Successfully"
                  )
    
# -------------------------
# VIEW DATA
# -------------------------
elif page == "View Data":

    st.header("Registered Wafers")

    wafer_df = pd.read_sql(
        "SELECT * FROM wafers",
        conn
    )

    st.dataframe(
        wafer_df,
        width="stretch"
    )

    st.header("Process History")

    process_df = pd.read_sql(
        "SELECT * FROM process_runs",
        conn
    )

    st.dataframe(
        process_df,
        width="stretch"
    )
# -------------------------
# Reports
# -------------------------
elif page == "Reports":

    st.markdown("""
    <div style="
    background:linear-gradient(90deg,#001F54,#034078,#1282A2);
    padding:25px;
    border-radius:20px;
    color:white;
    text-align:center;">
    <h1>📄 Laser Diode Report Center</h1>
    <p>Generate fabrication reports for complete production history</p>
    </div>
    """, unsafe_allow_html=True)


    report_type = st.radio(
        "Select Report Type",
        [
            "All Wafers",
            "Specific Wafer"
        ]
    )


    selected_wafer = None


    if report_type == "Specific Wafer":

        wafer_list = pd.read_sql(
            "SELECT wafer_id FROM wafers",
            conn
        )


        if len(wafer_list)==0:

            st.warning(
                "No wafers available"
            )

        else:

            selected_wafer = st.selectbox(
                "Select Wafer ID",
                wafer_list["wafer_id"]
            )



    if st.button(
        "🚀 Generate PDF Report"
    ):


        file = generate_pdf(
            selected_wafer
        )


        with open(file,"rb") as f:

            st.download_button(
                "⬇ Download PDF",
                f,
                file_name=file,
                mime="application/pdf"
            )
# -------------------------
# Delete Records
# -------------------------

elif page=="Delete Records":


    st.header("🗑 Delete MES Records")


    delete_type = st.selectbox(
        "Select Data",
        [
            "Delete Wafer",
            "Delete Process Record"
        ]
    )


    if delete_type=="Delete Wafer":

        wafers=pd.read_sql(
            "SELECT wafer_id FROM wafers",
            conn
        )


        if len(wafers)>0:

            wafer = st.selectbox(
                "Select Wafer",
                wafers["wafer_id"]
            )


            if st.button(
                "Delete Wafer"
            ):

                cursor.execute(
                    "DELETE FROM wafers WHERE wafer_id=?",
                    (wafer,)
                )


                cursor.execute(
                    "DELETE FROM process_runs WHERE wafer_id=?",
                    (wafer,)
                )


                conn.commit()


                st.success(
                    "Wafer deleted successfully"
                )



    else:

        records=pd.read_sql(
            "SELECT id,wafer_id,process_name FROM process_runs",
            conn
        )


        if len(records)>0:


            record_id=st.selectbox(
                "Select Process Record",
                records["id"]
            )


            if st.button(
                "Delete Process"
            ):


                cursor.execute(
                    "DELETE FROM process_runs WHERE id=?",
                    (record_id,)
                )


                conn.commit()


                st.success(
                    "Process record deleted"
                )
