import lucida_gui.app

def test_entrypoint_importable_without_display():
    assert callable(lucida_gui.app.main)
