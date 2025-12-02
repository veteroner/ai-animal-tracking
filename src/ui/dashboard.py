# src/ui/dashboard.py
"""
AI Animal Tracking System - Streamlit Dashboard
==============================================

Ana web arayüzü - gerçek zamanlı hayvan takip ve analiz dashboard'u.
"""

import streamlit as st
import cv2
import numpy as np
import time
from datetime import datetime, timedelta
import json
from pathlib import Path
import sys
import plotly.express as px
import plotly.graph_objects as go

# Proje kök dizinini path'e ekle
ROOT_DIR = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT_DIR))


# ===========================================
# Page Configuration
# ===========================================

st.set_page_config(
    page_title="AI Animal Tracking System",
    page_icon="🐄",
    layout="wide",
    initial_sidebar_state="expanded"
)


# ===========================================
# Custom CSS
# ===========================================

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .metric-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 1rem;
        text-align: center;
    }
    
    .status-active {
        color: #4CAF50;
        font-weight: bold;
    }
    
    .status-inactive {
        color: #f44336;
        font-weight: bold;
    }
    
    .status-warning {
        color: #FF9800;
        font-weight: bold;
    }
    
    .alert-critical {
        background-color: #FFEBEE;
        border-left: 4px solid #f44336;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .alert-warning {
        background-color: #FFF3E0;
        border-left: 4px solid #FF9800;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .alert-info {
        background-color: #E3F2FD;
        border-left: 4px solid #2196F3;
        padding: 1rem;
        margin: 0.5rem 0;
    }
    
    .camera-feed {
        border: 2px solid #1E88E5;
        border-radius: 10px;
        overflow: hidden;
    }
    
    .animal-card {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
</style>
""", unsafe_allow_html=True)


# ===========================================
# Session State Initialization
# ===========================================

if 'camera_active' not in st.session_state:
    st.session_state.camera_active = False
    
if 'selected_camera' not in st.session_state:
    st.session_state.selected_camera = None
    
if 'detection_enabled' not in st.session_state:
    st.session_state.detection_enabled = True
    
if 'tracking_enabled' not in st.session_state:
    st.session_state.tracking_enabled = True

if 'farm_mode' not in st.session_state:
    st.session_state.farm_mode = "cattle"  # cattle, poultry

if 'poultry_stats' not in st.session_state:
    st.session_state.poultry_stats = {
        "total_birds": 0,
        "eggs_today": 0,
        "health_alerts": 0,
    }


# ===========================================
# Mock Data (Development)
# ===========================================

def get_mock_animals():
    """Get mock animal data for development."""
    return [
        {
            "id": "ANM-001",
            "species": "cow",
            "name": "Sarıkız",
            "health_score": 92,
            "behavior": "eating",
            "last_seen": datetime.now() - timedelta(minutes=5),
            "location": "Bölge A"
        },
        {
            "id": "ANM-002",
            "species": "cow",
            "name": "Karabaş",
            "health_score": 78,
            "behavior": "resting",
            "last_seen": datetime.now() - timedelta(minutes=2),
            "location": "Bölge B"
        },
        {
            "id": "ANM-003",
            "species": "sheep",
            "name": "Pamuk",
            "health_score": 65,
            "behavior": "walking",
            "last_seen": datetime.now() - timedelta(minutes=15),
            "location": "Bölge A"
        },
        {
            "id": "ANM-004",
            "species": "cow",
            "name": "Boncuk",
            "health_score": 45,
            "behavior": "lying",
            "last_seen": datetime.now() - timedelta(minutes=1),
            "location": "Bölge C"
        },
    ]


def get_mock_alerts():
    """Get mock alert data for development."""
    return [
        {
            "id": "ALR-001",
            "severity": "critical",
            "title": "Düşük Sağlık Skoru",
            "message": "ANM-004 (Boncuk) sağlık skoru kritik seviyede: 45%",
            "timestamp": datetime.now() - timedelta(minutes=10),
            "acknowledged": False
        },
        {
            "id": "ALR-002",
            "severity": "warning",
            "title": "Düşük Aktivite",
            "message": "ANM-003 (Pamuk) son 2 saattir hareketsiz",
            "timestamp": datetime.now() - timedelta(hours=1),
            "acknowledged": False
        },
        {
            "id": "ALR-003",
            "severity": "info",
            "title": "Yeni Hayvan Algılandı",
            "message": "Bölge B'de yeni hayvan tespit edildi",
            "timestamp": datetime.now() - timedelta(hours=3),
            "acknowledged": True
        },
    ]


def get_mock_cameras():
    """Get mock camera data."""
    return [
        {"id": "CAM-001", "name": "Ana Ahır", "status": "active", "fps": 25},
        {"id": "CAM-002", "name": "Mera Alanı", "status": "active", "fps": 20},
        {"id": "CAM-003", "name": "Su Noktası", "status": "inactive", "fps": 0},
        {"id": "CAM-004", "name": "Giriş Kapısı", "status": "active", "fps": 30},
    ]


def get_mock_statistics():
    """Get mock statistics."""
    return {
        "total_animals": 156,
        "active_cameras": 3,
        "detections_today": 1245,
        "alerts_pending": 2,
        "avg_health_score": 82.5,
        "species_distribution": {
            "cow": 85,
            "sheep": 52,
            "goat": 19
        },
        "behavior_distribution": {
            "eating": 35,
            "resting": 45,
            "walking": 28,
            "standing": 32,
            "lying": 16
        }
    }


# ===========================================
# Sidebar
# ===========================================

with st.sidebar:
    st.image("https://via.placeholder.com/200x80?text=AI+Animal+Track", use_container_width=True)
    st.markdown("---")
    
    # Farm Mode Selection
    st.header("🏠 Çiftlik Modu")
    farm_mode = st.selectbox(
        "Mod Seçin:",
        ["🐄 Büyükbaş/Küçükbaş", "🐔 Kanatlı Kümes"],
        index=0 if st.session_state.farm_mode == "cattle" else 1,
        label_visibility="collapsed"
    )
    st.session_state.farm_mode = "cattle" if "Büyükbaş" in farm_mode else "poultry"
    
    st.markdown("---")
    
    # Navigation based on mode
    st.header("📍 Navigasyon")
    if st.session_state.farm_mode == "cattle":
        page = st.radio(
            "Sayfa Seçin:",
            ["🏠 Ana Sayfa", "📹 Kamera İzleme", "🐄 Hayvan Listesi", 
             "📊 Analitik", "🔔 Uyarılar", "⚙️ Ayarlar"],
            label_visibility="collapsed"
        )
    else:
        page = st.radio(
            "Sayfa Seçin:",
            ["🏠 Ana Sayfa", "📹 Kamera İzleme", "🐔 Kanatlı Listesi",
             "🥚 Yumurta Takibi", "📊 Analitik", "🔔 Uyarılar", "⚙️ Ayarlar"],
            label_visibility="collapsed"
        )
    
    st.markdown("---")
    
    # Quick Stats based on mode
    st.header("📈 Hızlı İstatistikler")
    stats = get_mock_statistics()
    
    col1, col2 = st.columns(2)
    if st.session_state.farm_mode == "cattle":
        with col1:
            st.metric("Toplam Hayvan", stats["total_animals"])
            st.metric("Aktif Kamera", stats["active_cameras"])
        with col2:
            st.metric("Bugünkü Tespit", stats["detections_today"])
            st.metric("Bekleyen Uyarı", stats["alerts_pending"])
    else:
        with col1:
            st.metric("🐔 Toplam Kanatlı", 250)
            st.metric("📹 Aktif Kamera", stats["active_cameras"])
        with col2:
            st.metric("🥚 Bugünkü Yumurta", 185)
            st.metric("⚠️ Sağlık Uyarısı", 3)
    
    st.markdown("---")
    
    # System Status
    st.header("🔧 Sistem Durumu")
    st.success("✅ API Aktif")
    st.success("✅ Model Yüklü")
    st.warning("⚠️ 1 Kamera Çevrimdışı")


# ===========================================
# Main Content
# ===========================================

# Header
st.markdown('<h1 class="main-header">🐄 AI Animal Tracking System</h1>', unsafe_allow_html=True)


# ===========================================
# Page: Home
# ===========================================

if page == "🏠 Ana Sayfa":
    
    # Metric Cards
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric(
            label="Toplam Hayvan",
            value=stats["total_animals"],
            delta="+3 bu hafta"
        )
        
    with col2:
        st.metric(
            label="Ortalama Sağlık",
            value=f"{stats['avg_health_score']:.1f}%",
            delta="2.3%"
        )
        
    with col3:
        st.metric(
            label="Aktif Kamera",
            value=f"{stats['active_cameras']}/4",
            delta="-1"
        )
        
    with col4:
        st.metric(
            label="Günlük Tespit",
            value=stats["detections_today"],
            delta="+15%"
        )
    
    st.markdown("---")
    
    # Main Layout
    col_main, col_side = st.columns([2, 1])
    
    with col_main:
        st.subheader("📹 Canlı Kamera Önizleme")
        
        # Kamera modu seçimi
        camera_mode = st.radio(
            "Kamera Kaynağı:",
            ["📷 Webcam (Anlık)", "🎥 Video Dosyası", "🖼️ Demo Modu"],
            horizontal=True
        )
        
        if camera_mode == "📷 Webcam (Anlık)":
            # Streamlit'in dahili kamera widget'ı
            camera_image = st.camera_input("Kameradan görüntü al")
            
            if camera_image is not None:
                # Görüntüyü işle
                import io
                from PIL import Image
                
                image = Image.open(camera_image)
                frame = np.array(image)
                
                # Tespit checkbox'ları
                col1, col2 = st.columns(2)
                with col1:
                    detection_on = st.checkbox("🔍 Tespit Aktif", value=True)
                with col2:
                    tracking_on = st.checkbox("📍 Takip Aktif", value=True)
                
                if detection_on:
                    # Yeşil çerçeve ekle (demo)
                    frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                    cv2.rectangle(frame_bgr, (10, 10), (frame.shape[1]-10, frame.shape[0]-10), 
                                 (0, 255, 0), 3)
                    cv2.putText(frame_bgr, "TESPIT AKTIF", (20, 40), 
                               cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                    frame = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
                
                st.image(frame, caption="İşlenmiş Görüntü", use_container_width=True)
                st.success("✅ Görüntü alındı! Yeni fotoğraf için tekrar tıklayın.")
            else:
                st.info("📸 Kameradan görüntü almak için yukarıdaki butona tıklayın")
                
        elif camera_mode == "🎥 Video Dosyası":
            # Video dosyası yükleme
            video_file = st.file_uploader("Video dosyası seçin", type=["mp4", "avi", "mov"])
            
            if video_file:
                st.video(video_file)
                st.success("✅ Video yüklendi")
            else:
                st.info("📁 Analiz için bir video dosyası yükleyin")
                
        else:  # Demo Modu
            # Demo görüntüsü
            mock_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            mock_frame[:] = (50, 50, 50)
            
            # Demo hayvan kutuları
            cv2.rectangle(mock_frame, (100, 150), (250, 350), (0, 255, 0), 2)
            cv2.putText(mock_frame, "Inek #1", (105, 145), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.rectangle(mock_frame, (300, 180), (450, 380), (0, 255, 0), 2)
            cv2.putText(mock_frame, "Inek #2", (305, 175), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
            
            cv2.rectangle(mock_frame, (480, 200), (600, 360), (0, 255, 255), 2)
            cv2.putText(mock_frame, "Koyun #1", (485, 195), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 255), 2)
            
            cv2.putText(mock_frame, "DEMO MODU - 3 Hayvan Tespit Edildi", (120, 450), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (200, 200, 200), 2)
            
            st.image(mock_frame, channels="BGR", use_container_width=True)
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Tespit", "3 hayvan")
            with col2:
                st.metric("İnek", "2")
            with col3:
                st.metric("Koyun", "1")
    
    with col_side:
        # Recent Alerts
        st.subheader("🔔 Son Uyarılar")
        
        alerts = get_mock_alerts()
        for alert in alerts[:3]:
            severity_class = f"alert-{alert['severity']}"
            status_icon = "❌" if not alert["acknowledged"] else "✅"
            
            st.markdown(f"""
            <div class="{severity_class}">
                <strong>{status_icon} {alert['title']}</strong><br>
                <small>{alert['message']}</small><br>
                <small style="color: gray;">{alert['timestamp'].strftime('%H:%M')}</small>
            </div>
            """, unsafe_allow_html=True)
        
        if st.button("Tüm Uyarıları Gör", use_container_width=True):
            st.session_state.page = "🔔 Uyarılar"
        
        st.markdown("---")
        
        # Species Distribution
        st.subheader("📊 Tür Dağılımı")
        
        import plotly.express as px
        
        species_data = stats["species_distribution"]
        fig = px.pie(
            values=list(species_data.values()),
            names=list(species_data.keys()),
            hole=0.4
        )
        fig.update_layout(
            margin=dict(l=0, r=0, t=0, b=0),
            height=200,
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=-0.3)
        )
        st.plotly_chart(fig, use_container_width=True)


# ===========================================
# Page: Camera Monitoring
# ===========================================

elif page == "📹 Kamera İzleme":
    st.header("📹 Kamera İzleme")
    
    cameras = get_mock_cameras()
    
    # Camera selection
    col1, col2 = st.columns([3, 1])
    
    with col1:
        selected_cam = st.selectbox(
            "Kamera Seçin:",
            options=[c["name"] for c in cameras],
            key="camera_select"
        )
    
    with col2:
        view_mode = st.radio(
            "Görünüm:",
            ["Tekli", "Grid"],
            horizontal=True
        )
    
    if view_mode == "Tekli":
        # Single camera view
        col_video, col_info = st.columns([3, 1])
        
        with col_video:
            # Large video placeholder
            frame = np.zeros((720, 1280, 3), dtype=np.uint8)
            frame[:] = (30, 30, 30)
            
            cv2.putText(frame, f"Kamera: {selected_cam}", 
                       (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            cv2.putText(frame, "Baglanti Bekleniyor...", 
                       (500, 360), cv2.FONT_HERSHEY_SIMPLEX, 1, (200, 200, 200), 2)
            
            st.image(frame, channels="BGR", use_container_width=True)
            
            # Controls
            ctrl1, ctrl2, ctrl3, ctrl4, ctrl5 = st.columns(5)
            with ctrl1:
                st.button("▶️ Başlat", key="start_single", use_container_width=True)
            with ctrl2:
                st.button("⏹️ Durdur", key="stop_single", use_container_width=True)
            with ctrl3:
                st.button("📸 Yakala", key="capture", use_container_width=True)
            with ctrl4:
                st.button("⏺️ Kaydet", key="record", use_container_width=True)
            with ctrl5:
                st.button("🔄 Yenile", key="refresh", use_container_width=True)
        
        with col_info:
            cam_data = next((c for c in cameras if c["name"] == selected_cam), cameras[0])
            
            st.subheader("📋 Kamera Bilgisi")
            
            status_color = "🟢" if cam_data["status"] == "active" else "🔴"
            st.markdown(f"**Durum:** {status_color} {cam_data['status'].capitalize()}")
            st.markdown(f"**ID:** {cam_data['id']}")
            st.markdown(f"**FPS:** {cam_data['fps']}")
            
            st.markdown("---")
            
            st.subheader("🎯 Tespit Ayarları")
            st.slider("Güven Eşiği", 0.0, 1.0, 0.5, key="conf_thresh")
            st.selectbox("Model", ["YOLOv8n", "YOLOv8s", "YOLOv8m"], key="model_select")
            st.checkbox("Takip Aktif", value=True, key="tracking_on")
            st.checkbox("Davranış Analizi", value=True, key="behavior_on")
            
    else:
        # Grid view
        st.subheader("🖥️ Çoklu Kamera Görünümü")
        
        cols = st.columns(2)
        for idx, camera in enumerate(cameras):
            with cols[idx % 2]:
                frame = np.zeros((240, 320, 3), dtype=np.uint8)
                frame[:] = (30, 30, 30)
                
                status_color = (0, 255, 0) if camera["status"] == "active" else (0, 0, 255)
                cv2.circle(frame, (300, 20), 8, status_color, -1)
                cv2.putText(frame, camera["name"], 
                           (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 1)
                
                if camera["status"] == "inactive":
                    cv2.putText(frame, "CEVRIMDISI", 
                               (100, 130), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
                else:
                    cv2.putText(frame, f"FPS: {camera['fps']}", 
                               (10, 230), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1)
                
                st.image(frame, channels="BGR", use_container_width=True)
                st.markdown(f"**{camera['name']}** - {camera['id']}")


# ===========================================
# Page: Animal List
# ===========================================

elif page == "🐄 Hayvan Listesi":
    st.header("🐄 Hayvan Listesi")
    
    animals = get_mock_animals()
    
    # Filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        species_filter = st.selectbox(
            "Tür Filtresi:",
            ["Tümü", "cow", "sheep", "goat"],
            key="species_filter"
        )
    
    with col2:
        behavior_filter = st.selectbox(
            "Davranış Filtresi:",
            ["Tümü", "eating", "resting", "walking", "lying", "standing"],
            key="behavior_filter"
        )
    
    with col3:
        health_filter = st.selectbox(
            "Sağlık Filtresi:",
            ["Tümü", "İyi (>80%)", "Orta (50-80%)", "Kritik (<50%)"],
            key="health_filter"
        )
    
    # Search
    search = st.text_input("🔍 Hayvan Ara (ID veya İsim):", key="animal_search")
    
    st.markdown("---")
    
    # Animal cards
    filtered_animals = animals
    
    if species_filter != "Tümü":
        filtered_animals = [a for a in filtered_animals if a["species"] == species_filter]
    
    if behavior_filter != "Tümü":
        filtered_animals = [a for a in filtered_animals if a["behavior"] == behavior_filter]
    
    if search:
        filtered_animals = [a for a in filtered_animals 
                          if search.lower() in a["id"].lower() or search.lower() in a["name"].lower()]
    
    if not filtered_animals:
        st.info("Filtrelere uygun hayvan bulunamadı.")
    else:
        cols = st.columns(2)
        for idx, animal in enumerate(filtered_animals):
            with cols[idx % 2]:
                # Determine health status color
                if animal["health_score"] >= 80:
                    health_color = "🟢"
                    health_status = "İyi"
                elif animal["health_score"] >= 50:
                    health_color = "🟡"
                    health_status = "Orta"
                else:
                    health_color = "🔴"
                    health_status = "Kritik"
                
                # Species emoji
                species_emoji = {"cow": "🐄", "sheep": "🐑", "goat": "🐐"}.get(animal["species"], "🐾")
                
                # Behavior translation
                behavior_tr = {
                    "eating": "Yemek Yiyor",
                    "resting": "Dinleniyor",
                    "walking": "Yürüyor",
                    "lying": "Yatıyor",
                    "standing": "Ayakta"
                }.get(animal["behavior"], animal["behavior"])
                
                with st.container():
                    st.markdown(f"""
                    <div class="animal-card">
                        <h3>{species_emoji} {animal['name']} ({animal['id']})</h3>
                        <p><strong>Tür:</strong> {animal['species'].capitalize()}</p>
                        <p><strong>Davranış:</strong> {behavior_tr}</p>
                        <p><strong>Sağlık:</strong> {health_color} {animal['health_score']}% ({health_status})</p>
                        <p><strong>Konum:</strong> {animal['location']}</p>
                        <p><small>Son Görülme: {animal['last_seen'].strftime('%H:%M')}</small></p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    col_btn1, col_btn2, col_btn3 = st.columns(3)
                    with col_btn1:
                        st.button("📊 Detay", key=f"detail_{animal['id']}", use_container_width=True)
                    with col_btn2:
                        st.button("📍 Takip", key=f"track_{animal['id']}", use_container_width=True)
                    with col_btn3:
                        st.button("📝 Düzenle", key=f"edit_{animal['id']}", use_container_width=True)


# ===========================================
# Page: Analytics
# ===========================================

elif page == "📊 Analitik":
    st.header("📊 Analitik Dashboard")
    
    # Date range selector
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("Başlangıç:", datetime.now() - timedelta(days=7))
    with col2:
        end_date = st.date_input("Bitiş:", datetime.now())
    
    st.markdown("---")
    
    # Charts row 1
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Günlük Tespit Sayısı")
        
        import plotly.graph_objects as go
        
        # Mock data
        days = [(datetime.now() - timedelta(days=x)).strftime('%d/%m') for x in range(7, -1, -1)]
        detections = [980, 1050, 1120, 890, 1200, 1150, 1245, 1300]
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=days, y=detections,
            mode='lines+markers',
            line=dict(color='#1E88E5', width=2),
            marker=dict(size=8)
        ))
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            xaxis_title="Tarih",
            yaxis_title="Tespit Sayısı"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Davranış Dağılımı")
        
        behavior_data = stats["behavior_distribution"]
        
        fig = px.bar(
            x=list(behavior_data.keys()),
            y=list(behavior_data.values()),
            color=list(behavior_data.keys()),
            labels={'x': 'Davranış', 'y': 'Hayvan Sayısı'}
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            showlegend=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Charts row 2
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("❤️ Sağlık Skoru Dağılımı")
        
        # Mock health distribution
        health_ranges = ["0-20", "20-40", "40-60", "60-80", "80-100"]
        health_counts = [2, 5, 15, 48, 86]
        
        fig = px.bar(
            x=health_ranges, y=health_counts,
            color=health_counts,
            color_continuous_scale=['red', 'orange', 'yellow', 'lightgreen', 'green'],
            labels={'x': 'Sağlık Skoru Aralığı', 'y': 'Hayvan Sayısı'}
        )
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            coloraxis_showscale=False
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🕐 Saatlik Aktivite")
        
        hours = list(range(24))
        activity = [5, 3, 2, 2, 3, 8, 25, 45, 55, 48, 42, 38,
                   35, 40, 45, 50, 55, 52, 48, 35, 25, 15, 10, 7]
        
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=hours, y=activity,
            marker_color='#1E88E5'
        ))
        fig.update_layout(
            margin=dict(l=20, r=20, t=20, b=20),
            height=300,
            xaxis_title="Saat",
            yaxis_title="Aktivite Skoru"
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Summary metrics
    st.markdown("---")
    st.subheader("📋 Özet İstatistikler")
    
    metrics_cols = st.columns(5)
    
    with metrics_cols[0]:
        st.metric("Ort. Günlük Tespit", "1,117", "+5.2%")
    with metrics_cols[1]:
        st.metric("Ort. Sağlık Skoru", "82.5%", "+1.3%")
    with metrics_cols[2]:
        st.metric("En Aktif Bölge", "Bölge A", "")
    with metrics_cols[3]:
        st.metric("Toplam Uyarı", "23", "-12%")
    with metrics_cols[4]:
        st.metric("Sistem Uptime", "99.8%", "")


# ===========================================
# Page: Alerts
# ===========================================

elif page == "🔔 Uyarılar":
    st.header("🔔 Uyarı Merkezi")
    
    alerts = get_mock_alerts()
    
    # Alert filters
    col1, col2, col3 = st.columns(3)
    
    with col1:
        severity_filter = st.multiselect(
            "Önem Derecesi:",
            ["critical", "warning", "info"],
            default=["critical", "warning", "info"]
        )
    
    with col2:
        status_filter = st.radio(
            "Durum:",
            ["Tümü", "Onaylanmamış", "Onaylanmış"],
            horizontal=True
        )
    
    with col3:
        st.button("✅ Tümünü Onayla", use_container_width=True)
    
    st.markdown("---")
    
    # Alert list
    filtered_alerts = [a for a in alerts if a["severity"] in severity_filter]
    
    if status_filter == "Onaylanmamış":
        filtered_alerts = [a for a in filtered_alerts if not a["acknowledged"]]
    elif status_filter == "Onaylanmış":
        filtered_alerts = [a for a in filtered_alerts if a["acknowledged"]]
    
    if not filtered_alerts:
        st.success("🎉 Bekleyen uyarı bulunmuyor!")
    else:
        for alert in filtered_alerts:
            severity_icons = {"critical": "🔴", "warning": "🟡", "info": "🔵"}
            severity_icon = severity_icons.get(alert["severity"], "⚪")
            
            severity_class = f"alert-{alert['severity']}"
            ack_status = "✅ Onaylandı" if alert["acknowledged"] else "❌ Bekliyor"
            
            col_alert, col_actions = st.columns([4, 1])
            
            with col_alert:
                st.markdown(f"""
                <div class="{severity_class}">
                    <h4>{severity_icon} {alert['title']}</h4>
                    <p>{alert['message']}</p>
                    <small>🕐 {alert['timestamp'].strftime('%d/%m/%Y %H:%M')} | {ack_status}</small>
                </div>
                """, unsafe_allow_html=True)
            
            with col_actions:
                if not alert["acknowledged"]:
                    st.button("✅ Onayla", key=f"ack_{alert['id']}", use_container_width=True)
                st.button("📋 Detay", key=f"det_{alert['id']}", use_container_width=True)
                st.button("🗑️ Sil", key=f"del_{alert['id']}", use_container_width=True)
    
    # Alert rules section
    st.markdown("---")
    st.subheader("⚙️ Uyarı Kuralları")
    
    rules = [
        {"name": "Kritik Sağlık Uyarısı", "condition": "Sağlık < 30%", "enabled": True},
        {"name": "Sağlık Uyarısı", "condition": "Sağlık < 60%", "enabled": True},
        {"name": "Topallık Tespiti", "condition": "Topallık Skoru > 2", "enabled": True},
        {"name": "Hareketsizlik", "condition": "2+ saat hareketsiz", "enabled": False},
        {"name": "Kamera Çevrimdışı", "condition": "Bağlantı kesildi", "enabled": True},
    ]
    
    for rule in rules:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.markdown(f"**{rule['name']}**")
        with col2:
            st.markdown(f"_{rule['condition']}_")
        with col3:
            st.checkbox("", value=rule["enabled"], key=f"rule_{rule['name']}")


# ===========================================
# Page: Settings
# ===========================================

elif page == "⚙️ Ayarlar":
    st.header("⚙️ Sistem Ayarları")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎥 Kamera", "🤖 Model", "🔔 Bildirimler", "💾 Veritabanı"])
    
    with tab1:
        st.subheader("Kamera Ayarları")
        
        st.text_input("Varsayılan Kamera URL:", placeholder="rtsp://...")
        st.slider("Maksimum FPS:", 1, 60, 30)
        st.slider("Buffer Boyutu:", 1, 100, 30)
        st.selectbox("Varsayılan Çözünürlük:", ["640x480", "1280x720", "1920x1080"])
        
        col1, col2 = st.columns(2)
        with col1:
            st.checkbox("Otomatik Yeniden Bağlan", value=True)
        with col2:
            st.number_input("Yeniden Bağlanma Gecikmesi (sn):", 1, 60, 5)
    
    with tab2:
        st.subheader("Model Ayarları")
        
        st.selectbox("Tespit Modeli:", ["YOLOv8n", "YOLOv8s", "YOLOv8m", "YOLOv8l", "YOLOv8x"])
        st.slider("Güven Eşiği:", 0.0, 1.0, 0.5, 0.05)
        st.slider("IOU Eşiği:", 0.0, 1.0, 0.45, 0.05)
        
        st.multiselect(
            "Tespit Edilecek Türler:",
            ["cow", "sheep", "goat", "horse", "dog", "cat", "bird"],
            default=["cow", "sheep", "goat"]
        )
        
        st.selectbox("İşlem Cihazı:", ["Auto", "CPU", "CUDA", "MPS"])
    
    with tab3:
        st.subheader("Bildirim Ayarları")
        
        st.checkbox("E-posta Bildirimleri", value=False)
        st.text_input("E-posta Adresi:", placeholder="admin@example.com")
        
        st.checkbox("Webhook Bildirimleri", value=False)
        st.text_input("Webhook URL:", placeholder="https://...")
        
        st.checkbox("Sesli Uyarılar", value=True)
        st.slider("Bildirim Bekleme Süresi (dk):", 1, 60, 5)
    
    with tab4:
        st.subheader("Veritabanı Ayarları")
        
        st.selectbox("Veritabanı Tipi:", ["SQLite", "PostgreSQL", "MySQL"])
        st.text_input("Bağlantı String:", value="sqlite:///data/tracking.db")
        
        col1, col2 = st.columns(2)
        with col1:
            st.button("🔄 Bağlantıyı Test Et", use_container_width=True)
        with col2:
            st.button("💾 Yedek Al", use_container_width=True)
        
        st.markdown("---")
        st.subheader("Veri Yönetimi")
        
        st.number_input("Veri Saklama Süresi (gün):", 1, 365, 30)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.button("🗑️ Eski Verileri Temizle", use_container_width=True)
        with col2:
            st.button("📤 Dışa Aktar", use_container_width=True)
        with col3:
            st.button("📥 İçe Aktar", use_container_width=True)
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 Ayarları Kaydet", use_container_width=True, type="primary"):
            st.success("✅ Ayarlar kaydedildi!")
    with col2:
        if st.button("🔄 Varsayılana Sıfırla", use_container_width=True):
            st.warning("⚠️ Tüm ayarlar varsayılana sıfırlanacak!")


# ===========================================
# Page: Poultry List (Kanatlı Modu)
# ===========================================

elif page == "🐔 Kanatlı Listesi":
    st.header("🐔 Kanatlı Hayvan Listesi")
    
    # Filtreler
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        poultry_type = st.selectbox("Tür:", ["Tümü", "Tavuk", "Horoz", "Hindi", "Kaz", "Ördek"])
    with col2:
        health_filter = st.selectbox("Sağlık:", ["Tümü", "Sağlıklı", "Hasta", "Stresli"])
    with col3:
        zone_filter = st.selectbox("Bölge:", ["Tümü", "Yemlik", "Suluk", "Tünek", "Yumurtlama Kutusu"])
    with col4:
        st.text_input("🔍 Ara:", placeholder="ID veya etiket...")
    
    # Mock kanatlı verileri
    poultry_data = [
        {"id": "TAV-001", "type": "Tavuk", "age": "8 ay", "health": "Sağlıklı", "zone": "Yemlik", "eggs_weekly": 5},
        {"id": "TAV-002", "type": "Tavuk", "age": "10 ay", "health": "Sağlıklı", "zone": "Tünek", "eggs_weekly": 6},
        {"id": "TAV-003", "type": "Tavuk", "age": "6 ay", "health": "Stresli", "zone": "Yumurtlama", "eggs_weekly": 3},
        {"id": "HOR-001", "type": "Horoz", "age": "12 ay", "health": "Sağlıklı", "zone": "Serbest Alan", "eggs_weekly": 0},
        {"id": "TAV-004", "type": "Tavuk", "age": "9 ay", "health": "Hasta", "zone": "Karantina", "eggs_weekly": 0},
        {"id": "HIN-001", "type": "Hindi", "age": "14 ay", "health": "Sağlıklı", "zone": "Serbest Alan", "eggs_weekly": 2},
    ]
    
    # Kanatlı kartları
    for i in range(0, len(poultry_data), 3):
        cols = st.columns(3)
        for j, col in enumerate(cols):
            if i + j < len(poultry_data):
                bird = poultry_data[i + j]
                with col:
                    health_color = "🟢" if bird["health"] == "Sağlıklı" else "🟡" if bird["health"] == "Stresli" else "🔴"
                    st.markdown(f"""
                    <div class="animal-card">
                        <h4>🐔 {bird['id']}</h4>
                        <p><strong>Tür:</strong> {bird['type']}</p>
                        <p><strong>Yaş:</strong> {bird['age']}</p>
                        <p><strong>Sağlık:</strong> {health_color} {bird['health']}</p>
                        <p><strong>Bölge:</strong> {bird['zone']}</p>
                        <p><strong>Haftalık Yumurta:</strong> 🥚 {bird['eggs_weekly']}</p>
                    </div>
                    """, unsafe_allow_html=True)


# ===========================================
# Page: Egg Tracking (Yumurta Takibi)
# ===========================================

elif page == "🥚 Yumurta Takibi":
    st.header("🥚 Yumurta Üretim Takibi")
    
    # Özet metrikler
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Bugün", "185 🥚", "+12")
    with col2:
        st.metric("Bu Hafta", "1,245 🥚", "+85")
    with col3:
        st.metric("Ort. Günlük", "178 🥚")
    with col4:
        st.metric("Üretim Oranı", "%74", "+2%")
    
    st.markdown("---")
    
    # Grafikler
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Haftalık Üretim")
        import pandas as pd
        
        days = ["Pazartesi", "Salı", "Çarşamba", "Perşembe", "Cuma", "Cumartesi", "Pazar"]
        eggs = [172, 185, 168, 192, 180, 175, 185]
        
        fig = px.bar(
            x=days, y=eggs,
            labels={"x": "Gün", "y": "Yumurta Sayısı"},
            color_discrete_sequence=["#FF9800"]
        )
        fig.update_layout(showlegend=False)
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🏠 Yumurtlama Kutusu Dağılımı")
        
        boxes = ["Kutu 1", "Kutu 2", "Kutu 3", "Kutu 4", "Kutu 5"]
        counts = [42, 38, 45, 35, 25]
        
        fig = px.pie(
            names=boxes, values=counts,
            color_discrete_sequence=px.colors.sequential.Oranges
        )
        st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    
    # Yumurta kalitesi
    st.subheader("📊 Yumurta Kalite Dağılımı")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Normal", "165 (%89)")
    with col2:
        st.metric("Yumuşak Kabuk", "12 (%6)")
    with col3:
        st.metric("Çift Sarılı", "5 (%3)")
    with col4:
        st.metric("Anormal", "3 (%2)")
    
    st.markdown("---")
    
    # Manuel kayıt
    st.subheader("➕ Manuel Yumurta Kaydı")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.selectbox("Yumurtlama Kutusu:", ["Kutu 1", "Kutu 2", "Kutu 3", "Kutu 4", "Kutu 5"])
    with col2:
        st.number_input("Yumurta Sayısı:", 1, 10, 1)
    with col3:
        st.selectbox("Kalite:", ["Normal", "Yumuşak Kabuk", "Çift Sarılı", "Kan Lekeli"])
    
    if st.button("💾 Kaydı Ekle", type="primary"):
        st.success("✅ Yumurta kaydı eklendi!")


# ===========================================
# Footer
# ===========================================

st.markdown("---")
footer_icon = "🐔" if st.session_state.farm_mode == "poultry" else "🐄"
st.markdown(
    f"""
    <div style='text-align: center; color: gray;'>
        <p>{footer_icon} AI Animal Tracking System v0.1.0</p>
        <p>© 2024 - Powered by YOLO, OpenCV & Streamlit</p>
    </div>
    """,
    unsafe_allow_html=True
)
