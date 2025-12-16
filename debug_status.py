import time
import importlib
m = importlib.import_module('streamlit_main')
# Wait a moment for DataManager to start websocket
time.sleep(2)
dm = m.st.session_state.data_manager
print('SYMBOLS attribute length:', len(dm.SYMBOLS))
print('get_connection_status():', dm.get_connection_status())
print('tick_count:', dm.tick_count)
print('available symbols from get_available_symbols():', dm.get_available_symbols())
