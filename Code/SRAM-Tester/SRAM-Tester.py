from machine import Pin
import time

# Pin definitions
A0 = Pin(0, Pin.OUT)
A1 = Pin(1, Pin.OUT)
A2 = Pin(2, Pin.OUT)
A3 = Pin(3, Pin.OUT)
A4 = Pin(4, Pin.OUT)
A5 = Pin(5, Pin.OUT)
A6 = Pin(6, Pin.OUT)
A7 = Pin(7, Pin.OUT)

DI1 = Pin(8, Pin.OUT)
DI2 = Pin(9, Pin.OUT)
DI3 = Pin(10, Pin.OUT)
DI4 = Pin(11, Pin.OUT)

DO1 = Pin(12, Pin.IN, Pin.PULL_DOWN)
DO2 = Pin(13, Pin.IN, Pin.PULL_DOWN)
DO3 = Pin(14, Pin.IN, Pin.PULL_DOWN)
DO4 = Pin(15, Pin.IN, Pin.PULL_DOWN)

CE1 = Pin(16, Pin.OUT, value=1)
CE2 = Pin(17, Pin.OUT, value=0)
WE = Pin(18, Pin.OUT, value=1)
OD = Pin(19, Pin.OUT, value=1)

# Put pins in lists for easy access
address_pins = [A0, A1, A2, A3, A4, A5, A6, A7]
data_in_pins = [DI1, DI2, DI3, DI4]
data_out_pins = [DO1, DO2, DO3, DO4]

def set_address(addr):
    """Set address on A0-A7"""
    for i in range(8):
        bit = (addr >> i) & 1
        address_pins[i].value(bit)

def set_data_in(value):
    """Set data on DI1-DI4"""
    for i in range(4):
        bit = (value >> i) & 1
        data_in_pins[i].value(bit)

def get_data_out():
    """Read data from DO1-DO4"""
    value = 0
    for i in range(4):
        bit = data_out_pins[i].value()
        value |= (bit << i)
    return value

def disable_chip():
    """Disable the chip"""
    CE1.value(1)
    CE2.value(0)
    OD.value(1)
    WE.value(1)

def enable_chip_for_write():
    """Enable chip for writing"""
    CE1.value(0)  # LOW = enabled
    CE2.value(1)  # HIGH = enabled
    WE.value(0)   # LOW = write mode
    OD.value(1)   # HIGH = output disabled

def enable_chip_for_read():
    """Enable chip for reading"""
    CE1.value(0)  # LOW = enabled
    CE2.value(1)  # HIGH = enabled
    WE.value(1)   # HIGH = read mode
    OD.value(0)   # LOW = output enabled

def write_nibble(addr, data):
    """Write 4-bit data to address"""
    # Disable chip first
    disable_chip()
    time.sleep_us(10)
    
    # Set address and data
    set_address(addr)
    set_data_in(data)
    time.sleep_us(10)
    
    # Enable for write
    enable_chip_for_write()
    time.sleep_us(10)
    
    # Hold write pulse
    WE.value(0)
    time.sleep_us(10)
    
    # End write
    WE.value(1)
    time.sleep_us(10)
    
    # Disable chip
    disable_chip()
    set_data_in(0)

def read_nibble(addr):
    """Read 4-bit data from address"""
    # Disable chip first
    disable_chip()
    time.sleep_us(10)
    
    # Set address
    set_address(addr)
    time.sleep_us(10)
    
    # Enable for read
    enable_chip_for_read()
    time.sleep_us(10)
    
    # Read data
    data = get_data_out()
    
    # Disable chip
    disable_chip()
    
    return data

def test_single_address():
    """Test writing and reading at address 0"""
    print("\n=== TEST SINGLE ADDRESS ===")
    
    test_addr = 0x00
    test_data = 0x5  # 0101
    
    print(f"Writing 0x{test_data:X} ({test_data:04b}) to address 0x{test_addr:02X}")
    write_nibble(test_addr, test_data)
    
    print(f"Reading from address 0x{test_addr:02X}")
    read_data = read_nibble(test_addr)
    
    print(f"Read: 0x{read_data:X} ({read_data:04b})")
    
    if read_data == test_data:
        print("✅ PASS: Data matches!")
    else:
        print(f"❌ FAIL: Expected 0x{test_data:X}, got 0x{read_data:X}")

def test_all_addresses():
    """Test all 256 addresses"""
    print("\n=== TEST ALL ADDRESSES ===")
    print("Writing 0101 to all addresses...")
    
    test_data = 0x5
    passed = 0
    
    for addr in range(256):
        write_nibble(addr, test_data)
        read_data = read_nibble(addr)
        
        if read_data == test_data:
            passed += 1
        
        if (addr + 1) % 32 == 0:
            print(f"  Tested {addr + 1}/256 addresses")
    
    print(f"\nResults: {passed}/256 addresses passed")
    
    if passed == 256:
        print("✅ ALL TESTS PASSED!")
    else:
        print(f"❌ {256 - passed} addresses failed")

def monitor_pins():
    """Monitor pin states continuously"""
    print("\n=== PIN MONITOR ===")
    print("Press Ctrl+C to stop")
    print("DO1-DO4 should show random data if chip is powered")
    
    try:
        while True:
            # Put chip in read mode
            enable_chip_for_read()
            
            # Read all pins
            addr_val = 0
            for i in range(8):
                addr_val |= (address_pins[i].value() << i)
            
            data_in_val = 0
            for i in range(4):
                data_in_val |= (data_in_pins[i].value() << i)
            
            data_out_val = get_data_out()
            
            print(f"Addr: 0x{addr_val:02X} | DI: 0x{data_in_val:X} | DO: 0x{data_out_val:X} ({DO4.value()}{DO3.value()}{DO2.value()}{DO1.value()}) | CE1:{CE1.value()} CE2:{CE2.value()} WE:{WE.value()} OD:{OD.value()}")
            time.sleep_ms(500)
            
    except KeyboardInterrupt:
        print("\nStopped monitoring")
        disable_chip()

def main():
    print("AM9101 SRAM TEST")
    print("=" * 40)
    
    # Always start with chip disabled
    disable_chip()
    
    try:
        # First, let's check if we can see any output
        print("\nChecking if chip outputs anything...")
        print("Enabling chip for read at address 0...")
        
        set_address(0x00)
        enable_chip_for_read()
        time.sleep_ms(100)
        
        data = get_data_out()
        print(f"DO pins: {DO4.value()}{DO3.value()}{DO2.value()}{DO1.value()}")
        print(f"Data output: 0x{data:X} ({data:04b})")
        
        disable_chip()
        
        if data == 0 and DO1.value() == 0 and DO2.value() == 0 and DO3.value() == 0 and DO4.value() == 0:
            print("\n⚠️  WARNING: All DO pins are reading 0.")
            print("Possible issues:")
            print("1. Chip not getting 5V power")
            print("2. No level shifters (Pico is 3.3V, chip needs 5V)")
            print("3. OD pin should be LOW (0) for reading")
            print("4. CE1 should be LOW (0) AND CE2 should be HIGH (1)")
        
        # Ask what to do next
        choice = input("\nChoose test:\n1. Single address test\n2. All addresses test\n3. Monitor pins\nEnter choice (1-3): ")
        
        if choice == "1":
            test_single_address()
        elif choice == "2":
            test_all_addresses()
        elif choice == "3":
            monitor_pins()
        else:
            print("Invalid choice")
    
    except Exception as e:
        print(f"Error: {e}")
    
    finally:
        disable_chip()
        print("\nChip disabled. Test complete.")

# Run the test
if __name__ == "__main__":
    main()