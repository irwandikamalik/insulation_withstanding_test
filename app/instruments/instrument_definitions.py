
# ============================================================
# INSTRUMENT DEFINITIONS
# ============================================================

INSTRUMENT_MODELS = {
    "WT310E": [
        ("measurement_function", "Measurement Function"),
        ("voltage_range", "Voltage Range"),
        ("current_range", "Current Range"),
        ("frequency_range", "Frequency Range"),
        ("measurement_interval", "Measurement Interval"),
        ("wiring_mode", "Wiring Mode"),
    ],

    "PCR2000": [
        ("output_voltage", "Output Voltage"),
        ("output_frequency", "Output Frequency"),
        ("current_limit", "Current Limit"),
        ("output_mode", "Output Mode"),
        ("output_state", "Output State"),
    ],

    "TOS9200": [
        ("test_mode", "Test Mode"),
        ("test_voltage", "Test Voltage"),
        ("upper_limit", "Upper Limit"),
        ("lower_limit", "Lower Limit"),
        ("test_time", "Test Time"),
        ("ramp_time", "Ramp Time"),
        ("discharge_time", "Discharge Time"),
    ],
}

INTERFACES = [
    "USB",
    "GPIB",
    "TCPIP",
    "Serial",
]
