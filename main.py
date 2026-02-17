!pip install ipyleaflet ipywidgets >/dev/null

import json
from ipyleaflet import Map, Marker, MarkerCluster, Icon, LegendControl
from ipywidgets import VBox, HBox, Button, Text, Output, Label, Dropdown
from IPython.display import display

DATA_FILE = "travel_pins.json"

# -------------------------
# Helpers for load/save
# -------------------------
def load_pins():
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return []

def save_pins(pins):
    with open(DATA_FILE, "w") as f:
        json.dump(pins, f)

# -------------------------
# Status-color mapping
# -------------------------
STATUS_COLORS = {
    "Visited": "green",
    "Want to visit": "blue",
    "Not interested": "red"
}

# -------------------------
# Map + UI state
# -------------------------
pins = load_pins()
m = Map(center=(20, 0), zoom=2)
markers = []
cluster = MarkerCluster(markers=())
m.add_layer(cluster)

status_out = Output()
popup_area = Output()

def log(msg):
    with status_out:
        print(msg)

def refresh_cluster():
    cluster.markers = tuple(markers)

# -------------------------
# Marker icon helper
# -------------------------
def icon_for_status(status):
    color = STATUS_COLORS.get(status, "blue")
    return Icon(icon="map-marker", marker_color=color, icon_color="white", prefix="fa")

# -------------------------
# Marker click popup
# -------------------------
def on_marker_click(marker):
    popup_area.clear_output()
    with popup_area:
        name_box = Text(value=marker.pin.get("name", ""), description="Name:")
        status_dropdown = Dropdown(
            options=list(STATUS_COLORS.keys()),
            value=marker.pin.get("status", "Want to visit"),
            description="Status:"
        )
        btn_update = Button(description="Update", button_style="info")
        btn_delete = Button(description="Delete", button_style="danger")
        btn_cancel = Button(description="Cancel")

        def do_update(b):
            marker.pin["name"] = name_box.value.strip()
            marker.pin["status"] = status_dropdown.value
            marker.title = marker.pin["name"]
            marker.icon = icon_for_status(marker.pin["status"])
            save_pins(pins)
            log(f"Updated pin: {marker.pin['name']} ({marker.pin['status']})")
            popup_area.clear_output()

        def do_delete(b):
            if marker.pin in pins:
                pins.remove(marker.pin)
            if marker in markers:
                markers.remove(marker)
            refresh_cluster()
            save_pins(pins)
            log(f"Deleted pin at {marker.pin['lat']:.4f}, {marker.pin['lon']:.4f}")
            popup_area.clear_output()

        def do_cancel(b):
            popup_area.clear_output()

        btn_update.on_click(do_update)
        btn_delete.on_click(do_delete)
        btn_cancel.on_click(do_cancel)

        display(VBox([name_box, status_dropdown, HBox([btn_update, btn_delete, btn_cancel])]))

# -------------------------
# Helpers to create markers
# -------------------------
def make_marker_for_pin(pin):
    mkr = Marker(
        location=(pin["lat"], pin["lon"]),
        title=pin.get("name", ""),
        icon=icon_for_status(pin.get("status", "Want to visit"))
    )
    mkr.pin = pin
    def _cb(**kwargs):
        on_marker_click(mkr)
    mkr.on_click(_cb)
    markers.append(mkr)

def add_pin_at(lat, lon, name=None, status="Want to visit"):
    if not name or not name.strip():
        name = f"Pin {len(pins)+1}"
    pin = {"name": name, "lat": lat, "lon": lon, "status": status}
    pins.append(pin)
    save_pins(pins)
    make_marker_for_pin(pin)
    refresh_cluster()
    log(f"Added pin: {name} ({status}) @ {lat:.4f}, {lon:.4f}")

# -------------------------
# Load existing pins
# -------------------------
for p in pins:
    make_marker_for_pin(p)
refresh_cluster()

# -------------------------
# Map click => add pin
# -------------------------
def handle_map_click(**kwargs):
    if kwargs.get("type") == "click":
        lat, lon = kwargs["coordinates"]
        add_pin_at(lat, lon)

m.on_interaction(handle_map_click)

# -------------------------
# Save button
# -------------------------
save_btn = Button(description="Save pins to file", button_style="success")
def on_save(b):
    save_pins(pins)
    log("Pins saved to file")
save_btn.on_click(on_save)

# -------------------------
# Add legend control
# -------------------------
legend_dict = {status: color for status, color in STATUS_COLORS.items()}
m.add_control(LegendControl(legend=legend_dict, position="bottomright"))

# -------------------------
# Show map + controls + logs
# -------------------------
display(VBox([m, HBox([save_btn]), popup_area, Label("Log:"), status_out]))
