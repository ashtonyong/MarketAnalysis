import streamlit as st
import streamlit.components.v1 as components
import os

st.title("Bi-Directional Sync Sandbox")

comp_dir = os.path.join(os.path.dirname(__file__), "test_comp")
vp_sync_component = components.declare_component("vp_sync_comp", path=comp_dir)

sync_data = vp_sync_component(default={"message": "Waiting for payload..."})

st.write("Data received from Component:", sync_data)

# Inject JS shell
shell_js = """
<script>
setTimeout(() => {
    console.log("[Shell] Injecting payload into component iframes...");
    
    // Broadcast to all iframes
    const iframes = window.parent.document.querySelectorAll('iframe');
    let injected = 0;
    iframes.forEach(iframe => {
        try {
            iframe.contentWindow.postMessage({
                type: "vp_sync",
                payload: { test_value: "HACKED_VIA_BIDIRECTIONAL_COMPONENT", timestamp: Date.now() }
            }, "*");
            injected++;
        } catch (e) {
            console.log("Failed to post message", e);
        }
    });
    console.log(`[Shell] Reached ${injected} iframes.`);
    
}, 4000);
</script>
"""
components.html(shell_js, height=0)
