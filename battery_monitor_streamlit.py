import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import numpy as np
import time
import json
from datetime import datetime, timedelta
import io
import base64

# Configure page
st.set_page_config(
    page_title="Battery Cell Monitoring System",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(135deg, #4f46e5, #7c3aed);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 700;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .metric-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        border-left: 4px solid;
        margin: 0.5rem 0;
    }
    
    .status-critical { border-left-color: #ef4444; }
    .status-warning { border-left-color: #f59e0b; }
    .status-normal { border-left-color: #10b981; }
    
    .task-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 12px;
        padding: 1rem;
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.1);
    }
    
    .alert-critical {
        background: rgba(239, 68, 68, 0.1);
        border-left: 4px solid #ef4444;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    .alert-warning {
        background: rgba(245, 158, 11, 0.1);
        border-left: 4px solid #f59e0b;
        padding: 1rem;
        border-radius: 8px;
        margin: 0.5rem 0;
    }
    
    body {
        background: linear-gradient(135deg, #0a0e1a, #1a1f2e);
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
def init_session_state():
    if 'cells_data' not in st.session_state:
        st.session_state.cells_data = []
    if 'tasks_data' not in st.session_state:
        st.session_state.tasks_data = []
    if 'monitoring_active' not in st.session_state:
        st.session_state.monitoring_active = False
    if 'session_data' not in st.session_state:
        st.session_state.session_data = []
    if 'previous_session_data' not in st.session_state:
        st.session_state.previous_session_data = []
    if 'bench_name' not in st.session_state:
        st.session_state.bench_name = ""
    if 'group_number' not in st.session_state:
        st.session_state.group_number = ""

# Cell type configurations
CELL_TYPES = {
    "LFP": {
        "name": "Lithium Iron Phosphate",
        "nominal_voltage": 3.2,
        "minimum_voltage": 2.8,
        "maximum_voltage": 3.6,
        "charge_time": 90,
        "discharge_time": 180
    },
    "NMC": {
        "name": "Nickel Manganese Cobalt",
        "nominal_voltage": 3.6,
        "minimum_voltage": 3.2,
        "maximum_voltage": 4.0,
        "charge_time": 120,
        "discharge_time": 240
    },
    "LCO": {
        "name": "Lithium Cobalt Oxide",
        "nominal_voltage": 3.8,
        "minimum_voltage": 3.0,
        "maximum_voltage": 4.2,
        "charge_time": 100,
        "discharge_time": 200
    }
}

def generate_cell_data(cell_type):
    """Generate realistic cell data based on type"""
    specs = CELL_TYPES[cell_type]
    base_voltage = specs["nominal_voltage"]
    voltage_variation = (np.random.random() - 0.5) * 0.2
    voltage = np.clip(base_voltage + voltage_variation, 
                     specs["minimum_voltage"], 
                     specs["maximum_voltage"])
    
    current = max(0.1, 0.8 + (np.random.random() - 0.5) * 0.5)
    temperature = 25 + np.random.random() * 20
    capacity = voltage * current
    
    voltage_range = specs["maximum_voltage"] - specs["minimum_voltage"]
    soc = ((voltage - specs["minimum_voltage"]) / voltage_range) * 100
    
    return {
        "voltage": round(voltage, 2),
        "current": round(current, 2),
        "temperature": round(temperature, 1),
        "capacity": round(capacity, 2),
        "soc": round(soc, 1),
        "timestamp": datetime.now()
    }

def get_cell_status(voltage, temperature, cell_type):
    """Determine cell status based on parameters"""
    specs = CELL_TYPES[cell_type]
    
    if voltage <= specs["minimum_voltage"] * 1.1 or temperature > 45:
        return {"status": "🚨 Critical", "color": "critical"}
    elif voltage <= specs["minimum_voltage"] * 1.2 or temperature > 40:
        return {"status": "⚠️ Warning", "color": "warning"}
    elif voltage >= specs["maximum_voltage"] * 0.9:
        return {"status": "🔋 High", "color": "normal"}
    else:
        return {"status": "🟢 Normal", "color": "normal"}

def create_voltage_chart(cells_data):
    """Create voltage monitoring chart"""
    if not cells_data:
        return go.Figure()
    
    fig = go.Figure()
    
    for i, cell in enumerate(cells_data):
        fig.add_trace(go.Scatter(
            x=[cell["timestamp"]],
            y=[cell["voltage"]],
            mode='markers+lines',
            name=cell["name"],
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="Cell Voltages",
        xaxis_title="Time",
        yaxis_title="Voltage (V)",
        template="plotly_dark",
        height=400
    )
    
    return fig

def create_temperature_chart(cells_data):
    """Create temperature monitoring chart"""
    if not cells_data:
        return go.Figure()
    
    fig = go.Figure()
    
    for i, cell in enumerate(cells_data):
        fig.add_trace(go.Scatter(
            x=[cell["timestamp"]],
            y=[cell["temperature"]],
            mode='markers+lines',
            name=cell["name"],
            line=dict(width=3),
            marker=dict(size=8)
        ))
    
    fig.update_layout(
        title="Temperature Monitoring",
        xaxis_title="Time",
        yaxis_title="Temperature (°C)",
        template="plotly_dark",
        height=400
    )
    
    return fig

def create_status_pie_chart(cells_data):
    """Create status distribution pie chart"""
    if not cells_data:
        return go.Figure()
    
    status_counts = {'Normal': 0, 'Warning': 0, 'Critical': 0}
    
    for cell in cells_data:
        status = get_cell_status(cell["voltage"], cell["temperature"], cell["type"])
        if status["color"] == "critical":
            status_counts['Critical'] += 1
        elif status["color"] == "warning":
            status_counts['Warning'] += 1
        else:
            status_counts['Normal'] += 1
    
    fig = go.Figure(data=[go.Pie(
        labels=list(status_counts.keys()),
        values=list(status_counts.values()),
        hole=0.3,
        marker_colors=['#10b981', '#f59e0b', '#ef4444']
    )])
    
    fig.update_layout(
        title="Cell Status Distribution",
        template="plotly_dark",
        height=400
    )
    
    return fig

def create_comparison_chart(current_data, previous_data):
    """Create session comparison chart"""
    if not current_data or not previous_data:
        return go.Figure()
    
    current_avg = calculate_session_averages(current_data)
    previous_avg = calculate_session_averages(previous_data)
    
    metrics = ['Voltage', 'Temperature', 'SOC', 'Capacity']
    current_values = [current_avg['voltage'], current_avg['temperature'], 
                     current_avg['soc'], current_avg['capacity']]
    previous_values = [previous_avg['voltage'], previous_avg['temperature'], 
                      previous_avg['soc'], previous_avg['capacity']]
    
    fig = go.Figure(data=[
        go.Bar(name='Current Session', x=metrics, y=current_values, 
               marker_color='#4f46e5'),
        go.Bar(name='Previous Session', x=metrics, y=previous_values, 
               marker_color='#7c3aed')
    ])
    
    fig.update_layout(
        title="Session Comparison",
        template="plotly_dark",
        height=400,
        barmode='group'
    )
    
    return fig

def calculate_session_averages(session_data):
    """Calculate average values for a session"""
    if not session_data:
        return {'voltage': 0, 'temperature': 0, 'soc': 0, 'capacity': 0}
    
    # If session_data contains historical data points
    if isinstance(session_data[0], dict) and 'cells' in session_data[0]:
        all_cells = []
        for data_point in session_data:
            all_cells.extend(data_point['cells'])
        cells_data = all_cells
    else:
        cells_data = session_data
    
    if not cells_data:
        return {'voltage': 0, 'temperature': 0, 'soc': 0, 'capacity': 0}
    
    return {
        'voltage': round(np.mean([cell['voltage'] for cell in cells_data]), 2),
        'temperature': round(np.mean([cell['temperature'] for cell in cells_data]), 1),
        'soc': round(np.mean([cell['soc'] for cell in cells_data]), 1),
        'capacity': round(np.mean([cell['capacity'] for cell in cells_data]), 2)
    }

def export_to_csv(session_data, cells_data, tasks_data):
    """Export data to CSV format"""
    data_rows = []
    
    if session_data:
        for session in session_data:
            timestamp = session['timestamp']
            active_task = next((task for task in session.get('tasks', []) 
                              if task.get('status') == 'running'), None)
            
            for cell in session['cells']:
                status = get_cell_status(cell['voltage'], cell['temperature'], cell['type'])
                row = {
                    'Timestamp': timestamp,
                    'Cell Name': cell['name'],
                    'Type': cell['type'],
                    'Voltage (V)': cell['voltage'],
                    'Current (A)': cell['current'],
                    'Temperature (°C)': cell['temperature'],
                    'Capacity (Wh)': cell['capacity'],
                    'SOC (%)': cell['soc'],
                    'Status': status['status'],
                    'Active Task': active_task['type'] if active_task else 'None',
                    'Task Progress (%)': active_task.get('progress', 0) if active_task else 0
                }
                data_rows.append(row)
    
    return pd.DataFrame(data_rows)

def main():
    init_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">⚡ Battery Cell Monitoring & Task Management System</h1>', 
                unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; color: #94a3b8; font-size: 1.1rem;">Advanced real-time monitoring with intelligent task automation and comprehensive analytics</p>', 
                unsafe_allow_html=True)
    
    # Sidebar Configuration
    with st.sidebar:
        st.header("🏭 Bench Configuration")
        
        bench_name = st.text_input("Bench Name", value=st.session_state.bench_name)
        group_number = st.text_input("Group Number", value=st.session_state.group_number)
        
        if bench_name != st.session_state.bench_name:
            st.session_state.bench_name = bench_name
        if group_number != st.session_state.group_number:
            st.session_state.group_number = group_number
        
        st.divider()
        
        # Cell Management
        st.header("🔋 Cell Management")
        
        num_cells = st.number_input("Number of Cells", min_value=1, max_value=20, value=1)
        default_cell_type = st.selectbox("Default Cell Type", 
                                        options=list(CELL_TYPES.keys()),
                                        format_func=lambda x: f"{x} - {CELL_TYPES[x]['name']}")
        
        if st.button("Generate Cells", type="primary"):
            st.session_state.cells_data = []
            for i in range(num_cells):
                cell_data = generate_cell_data(default_cell_type)
                cell_data.update({
                    "id": i + 1,
                    "name": f"Cell_{i + 1}",
                    "type": default_cell_type
                })
                st.session_state.cells_data.append(cell_data)
            st.success(f"Generated {num_cells} cells successfully!")
            st.rerun()
        
        st.divider()
        
        # Task Management
        st.header("⚙️ Task Management")
        
        num_tasks = st.number_input("Number of Tasks", min_value=1, max_value=10, value=1)
        
        if st.button("Configure Tasks"):
            st.session_state.show_task_config = True
        
        st.divider()
        
        # Control Panel
        st.header("🎮 Control Panel")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if not st.session_state.monitoring_active:
                if st.button("🔴 Start Monitoring", type="primary"):
                    st.session_state.monitoring_active = True
                    st.success("Monitoring started!")
                    st.rerun()
            else:
                if st.button("⏸️ Pause Monitoring", type="secondary"):
                    st.session_state.monitoring_active = False
                    st.warning("Monitoring paused")
                    st.rerun()
        
        with col2:
            if st.button("🔄 Update Data"):
                if st.session_state.cells_data:
                    for cell in st.session_state.cells_data:
                        new_data = generate_cell_data(cell["type"])
                        cell.update(new_data)
                    
                    # Store session data
                    st.session_state.session_data.append({
                        'timestamp': datetime.now(),
                        'cells': st.session_state.cells_data.copy(),
                        'tasks': st.session_state.tasks_data.copy()
                    })
                    
                    st.success("Data updated!")
                    st.rerun()
        
        if st.button("📊 Export CSV"):
            if st.session_state.session_data:
                df = export_to_csv(st.session_state.session_data, 
                                 st.session_state.cells_data, 
                                 st.session_state.tasks_data)
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name=f"battery_monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv"
                )
            else:
                st.error("No data available to export")
        
        col3, col4 = st.columns(2)
        with col3:
            if st.button("💾 Save Session"):
                session_data = {
                    'name': f"Session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                    'timestamp': datetime.now().isoformat(),
                    'bench_info': {
                        'name': st.session_state.bench_name,
                        'group': st.session_state.group_number
                    },
                    'cells_data': st.session_state.cells_data,
                    'tasks_data': st.session_state.tasks_data,
                    'session_data': st.session_state.session_data
                }
                
                # In a real app, you'd save this to a database or file
                st.success("Session saved! (In production, this would be saved to storage)")
        
        with col4:
            if st.button("📂 Load Session"):
                # In a real app, you'd load from storage
                st.info("Session loading feature would be implemented with proper storage backend")
    
    # Task Configuration Modal (using expander as modal alternative)
    if hasattr(st.session_state, 'show_task_config') and st.session_state.show_task_config:
        with st.expander("Configure Tasks", expanded=True):
            st.subheader("Task Configuration")
            
            tasks = []
            for i in range(num_tasks):
                st.write(f"**Task {i + 1}**")
                col1, col2 = st.columns(2)
                
                with col1:
                    task_type = st.selectbox(f"Task Type {i + 1}", 
                                           ["CC_CV", "IDLE", "CC_CD"], 
                                           key=f"task_type_{i}")
                
                with col2:
                    duration = st.number_input(f"Duration (seconds) {i + 1}", 
                                             min_value=1, value=300, 
                                             key=f"duration_{i}")
                
                task = {
                    'id': i + 1,
                    'type': task_type,
                    'duration': duration,
                    'progress': 0,
                    'status': 'pending',
                    'start_time': None,
                    'end_time': None
                }
                
                # Task-specific parameters
                if task_type == "CC_CV":
                    col3, col4 = st.columns(2)
                    with col3:
                        task['cccp'] = st.text_input(f"CC/CP Value {i + 1}", 
                                                   value="2A", key=f"cccp_{i}")
                        task['cv_voltage'] = st.number_input(f"CV Voltage {i + 1}", 
                                                           value=3.6, key=f"cv_voltage_{i}")
                    with col4:
                        task['current'] = st.number_input(f"Current {i + 1}", 
                                                        value=1.0, key=f"current_{i}")
                        task['capacity'] = st.number_input(f"Capacity {i + 1}", 
                                                         value=2.5, key=f"capacity_{i}")
                
                elif task_type == "CC_CD":
                    col3, col4 = st.columns(2)
                    with col3:
                        task['cccp'] = st.text_input(f"CC/CP Value {i + 1}", 
                                                   value="2A", key=f"cccp_cd_{i}")
                    with col4:
                        task['voltage'] = st.number_input(f"Discharge Voltage {i + 1}", 
                                                        value=2.8, key=f"voltage_{i}")
                        task['capacity'] = st.number_input(f"Capacity {i + 1}", 
                                                         value=2.5, key=f"capacity_cd_{i}")
                
                tasks.append(task)
                st.divider()
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("Cancel Tasks"):
                    st.session_state.show_task_config = False
                    st.rerun()
            
            with col2:
                if st.button("Save Tasks", type="primary"):
                    st.session_state.tasks_data = tasks
                    st.session_state.show_task_config = False
                    st.success(f"Configured {len(tasks)} tasks successfully!")
                    st.rerun()
    
    # Main Content Area
    
    # Alerts Section
    if st.session_state.cells_data:
        critical_cells = []
        warning_cells = []
        
        for cell in st.session_state.cells_data:
            status = get_cell_status(cell["voltage"], cell["temperature"], cell["type"])
            if status["color"] == "critical":
                critical_cells.append(cell)
            elif status["color"] == "warning":
                warning_cells.append(cell)
        
        if critical_cells or warning_cells:
            st.subheader("🚨 System Alerts")
            
            if critical_cells:
                st.markdown('<div class="alert-critical">', unsafe_allow_html=True)
                st.error("**🚨 Critical Alerts**")
                for cell in critical_cells:
                    st.write(f"**{cell['name']}**: {cell['voltage']}V, {cell['temperature']}°C - Immediate attention required!")
                st.markdown('</div>', unsafe_allow_html=True)
            
            if warning_cells:
                st.markdown('<div class="alert-warning">', unsafe_allow_html=True)
                st.warning("**⚠️ Warnings**")
                for cell in warning_cells:
                    st.write(f"**{cell['name']}**: {cell['voltage']}V, {cell['temperature']}°C - Monitor closely")
                st.markdown('</div>', unsafe_allow_html=True)
    
    # System Overview
    st.subheader("📊 System Overview")
    
    if st.session_state.cells_data:
        # Calculate metrics
        total_cells = len(st.session_state.cells_data)
        avg_voltage = np.mean([cell["voltage"] for cell in st.session_state.cells_data])
        avg_temperature = np.mean([cell["temperature"] for cell in st.session_state.cells_data])
        total_capacity = sum([cell["capacity"] for cell in st.session_state.cells_data])
        avg_soc = np.mean([cell["soc"] for cell in st.session_state.cells_data])
        
        # Display metrics
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            st.metric("Total Cells", total_cells)
        with col2:
            st.metric("Avg Voltage", f"{avg_voltage:.2f}V")
        with col3:
            st.metric("Avg Temperature", f"{avg_temperature:.1f}°C")
        with col4:
            st.metric("Total Capacity", f"{total_capacity:.2f}Wh")
        with col5:
            st.metric("Avg SOC", f"{avg_soc:.1f}%")
    else:
        st.info("👈 Configure cells from the sidebar to start monitoring")
    
    # Task Status
    if st.session_state.tasks_data:
        st.subheader("⚙️ Task Status")
        
        for task in st.session_state.tasks_data:
            with st.container():
                st.markdown('<div class="task-card">', unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns([2, 1, 1])
                
                with col1:
                    status_icon = "⏳" if task["status"] == "pending" else "▶️" if task["status"] == "running" else "✅"
                    st.write(f"**{task['type']}** {status_icon} {task['status'].upper()}")
                
                with col2:
                    st.write(f"Task {task['id']}")
                
                with col3:
                    st.write(f"Duration: {task['duration']}s")
                
                # Progress bar
                progress = task.get('progress', 0)
                st.progress(progress / 100)
                
                # Additional task details
                if task['type'] == 'CC_CV':
                    st.write(f"CC/CP: {task.get('cccp', 'N/A')}, CV: {task.get('cv_voltage', 'N/A')}V")
                elif task['type'] == 'CC_CD':
                    st.write(f"CC/CP: {task.get('cccp', 'N/A')}, Voltage: {task.get('voltage', 'N/A')}V")
                
                st.markdown('</div>', unsafe_allow_html=True)
    
    # Data Visualization Tabs
    st.subheader("📈 Data Visualization")
    
    tab1, tab2, tab3, tab4 = st.tabs(["Cell Data", "Charts", "Comparison", "Analytics"])
    
    with tab1:
        if st.session_state.cells_data:
            # Create dataframe for display
            display_data = []
            for cell in st.session_state.cells_data:
                status = get_cell_status(cell["voltage"], cell["temperature"], cell["type"])
                display_data.append({
                    "Cell Name": cell["name"],
                    "Type": cell["type"],
                    "Voltage (V)": cell["voltage"],
                    "Current (A)": cell["current"],
                    "Temperature (°C)": cell["temperature"],
                    "Capacity (Wh)": cell["capacity"],
                    "SOC (%)": cell["soc"],
                    "Status": status["status"],
                    "Last Updated": cell["timestamp"].strftime("%H:%M:%S")
                })
            
            df = pd.DataFrame(display_data)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("👈 Configure cells from the sidebar to start monitoring")
    
    with tab2:
        if st.session_state.cells_data:
            col1, col2 = st.columns(2)
            
            with col1:
                voltage_chart = create_voltage_chart(st.session_state.cells_data)
                st.plotly_chart(voltage_chart, use_container_width=True)
            
            with col2:
                temperature_chart = create_temperature_chart(st.session_state.cells_data)
                st.plotly_chart(temperature_chart, use_container_width=True)
        else:
            st.info("No data available for charts")
    
    with tab3:
        st.write("**Session Comparison**")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Load Previous Data"):
                # In a real app, this would load from storage
                st.info("Previous data loading would be implemented with proper storage backend")
        
        with col2:
            if st.button("Compare Sessions"):
                if st.session_state.session_data and st.session_state.previous_session_data:
                    comparison_chart = create_comparison_chart(
                        st.session_state.session_data, 
                        st.session_state.previous_session_data
                    )
                    st.plotly_chart(comparison_chart, use_container_width=True)
                else:
                    st.warning("Current and previous session data required for comparison")
    
    with tab4:
        if st.session_state.cells_data:
            col1, col2 = st.columns(2)
            
            with col1:
                pie_chart = create_status_pie_chart(st.session_state.cells_data)
                st.plotly_chart(pie_chart, use_container_width=True)
            
            with col2:
                # Time series chart for SOC
                if st.session_state.session_data:
                    timestamps = [data['timestamp'] for data in st.session_state.session_data]
                    avg_socs = []
                    
                    for data in st.session_state.session_data:
                        if data['cells']:
                            avg_soc = np.mean([cell['soc'] for cell in data['cells']])
                            avg_socs.append(avg_soc)
                        else:
                            avg_socs.append(0)
                    
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(
                        x=timestamps,
                        y=avg_socs,
                        mode='lines+markers',
                        name='Average SOC',
                        line=dict(color='#4f46e5', width=3)
                    ))
                    
                    fig.update_layout(
                        title="State of Charge Over Time",
                        xaxis_title="Time",
                        yaxis_title="SOC (%)",
                        template="plotly_dark",
                        height=400
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.info("No historical data available")
        else:
            st.info("No data available for analytics")
    
    # Auto-refresh when monitoring is active
    if st.session_state.monitoring_active:
        time.sleep(3)
        st.rerun()

if __name__ == "__main__":
    main()
