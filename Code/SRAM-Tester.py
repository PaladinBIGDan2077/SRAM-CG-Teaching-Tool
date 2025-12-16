from machine import Pin
import time

class AM9101_SRAM:
    """
    AMD AM9101 SRAM Controller for Raspberry Pi Pico
    256 x 4-bit static RAM
    """
    
    def __init__(self, address_pins, data_pin, ce_pin, we_pin, oe_pin):
        """
        Initialize SRAM interface
        
        Args:
            address_pins: List of GPIO pins for A0-A9 (10 address lines)
            data_pin: GPIO pin for I/O (data line)
            ce_pin: Chip Enable (active LOW)
            we_pin: Write Enable (active LOW)
            oe_pin: Output Enable (active LOW)
        """
        # Address pins (A0-A9 = 10 pins for 1024 addresses)
        self.address_pins = [Pin(pin, Pin.OUT) for pin in address_pins]
        
        # Data pin (bidirectional)
        self.data_pin = Pin(data_pin, Pin.OUT)
        self.data_pin_value = 0
        
        # Control pins
        self.ce = Pin(ce_pin, Pin.OUT, value=1)  # Active LOW, start disabled
        self.we = Pin(we_pin, Pin.OUT, value=1)  # Active LOW
        self.oe = Pin(oe_pin, Pin.OUT, value=1)  # Active LOW
        
        # Timing parameters (adjust based on your SRAM specs)
        self.write_delay = 0.001  # 1ms delay for writes
        self.read_delay = 0.001   # 1ms delay for reads
        
        print("AM9101 SRAM Initialized")
    
    def set_address(self, address):
        """Set the 10-bit address on address pins"""
        if address < 0 or address > 1023:
            raise ValueError("Address must be between 0 and 1023")
        
        for i in range(10):
            bit = (address >> i) & 0x01
            self.address_pins[i].value(bit)
    
    def write_bit(self, address, bit_value):
        """
        Write a single bit to the specified address
        
        Args:
            address: 0-1023
            bit_value: 0 or 1
        """
        if bit_value not in (0, 1):
            raise ValueError("Bit value must be 0 or 1")
        
        # Set address
        self.set_address(address)
        
        # Set data pin as output with the value to write
        self.data_pin.init(Pin.OUT)
        self.data_pin.value(bit_value)
        
        # Enable chip (active LOW)
        self.ce.value(0)
        
        # Wait for address/data to stabilize
        time.sleep(0.001)
        
        # Start write cycle (WE active LOW)
        self.we.value(0)
        
        # Hold write pulse (consult datasheet for minimum pulse width)
        time.sleep(self.write_delay)
        
        # End write cycle
        self.we.value(1)
        
        # Disable chip
        self.ce.value(1)
        
        # Reset data pin
        self.data_pin.value(0)
        
        self.data_pin_value = bit_value
    
    def read_bit(self, address):
        """
        Read a single bit from the specified address
        
        Returns:
            The bit value (0 or 1) read from SRAM
        """
        # Set address
        self.set_address(address)
        
        # Enable chip (active LOW)
        self.ce.value(0)
        
        # Enable output (active LOW)
        self.oe.value(0)
        
        # Configure data pin as input
        self.data_pin.init(Pin.IN, Pin.PULL_DOWN)
        
        # Wait for data to stabilize
        time.sleep(self.read_delay)
        
        # Read the bit
        bit_value = self.data_pin.value()
        
        # Disable output and chip
        self.oe.value(1)
        self.ce.value(1)
        
        # Configure data pin back as output for safety
        self.data_pin.init(Pin.OUT)
        self.data_pin.value(0)
        
        return bit_value
    
    def test_pattern(self, pattern_type="walking_one"):
        """
        Test the SRAM with various patterns
        
        Args:
            pattern_type: "walking_one", "alternating", "all_ones", "all_zeros"
        
        Returns:
            Dictionary with test results
        """
        print(f"\nRunning {pattern_type} test pattern...")
        
        test_data = []
        failures = []
        
        # Generate test pattern
        if pattern_type == "walking_one":
            # Walking 1 pattern (1 bit set at a time across 10 bits, repeated)
            for addr in range(1024):
                bit_value = (addr % 10 == 0)  # Set bit every 10 addresses
                test_data.append((addr, int(bit_value)))
        
        elif pattern_type == "alternating":
            # Alternating 0/1 pattern
            for addr in range(1024):
                bit_value = addr % 2
                test_data.append((addr, bit_value))
        
        elif pattern_type == "all_ones":
            # All 1's
            for addr in range(1024):
                test_data.append((addr, 1))
        
        elif pattern_type == "all_zeros":
            # All 0's
            for addr in range(1024):
                test_data.append((addr, 0))
        
        else:
            raise ValueError(f"Unknown pattern type: {pattern_type}")
        
        # Write test pattern
        for addr, bit in test_data:
            self.write_bit(addr, bit)
        
        # Read back and verify
        for addr, expected_bit in test_data:
            actual_bit = self.read_bit(addr)
            if actual_bit != expected_bit:
                failures.append((addr, expected_bit, actual_bit))
        
        # Print results
        total_tests = len(test_data)
        passed = total_tests - len(failures)
        
        print(f"Results: {passed}/{total_tests} passed")
        
        if failures:
            print("Failures detected:")
            for addr, expected, actual in failures[:10]:  # Show first 10 failures
                print(f"  Address 0x{addr:03X} ({addr:04d}): Expected {expected}, Got {actual}")
            if len(failures) > 10:
                print(f"  ... and {len(failures) - 10} more failures")
        
        return {
            "total": total_tests,
            "passed": passed,
            "failed": len(failures),
            "failures": failures
        }
    
    def memory_dump(self, start_addr=0, end_addr=31):
        """
        Dump memory contents in a readable format
        
        Args:
            start_addr: Starting address (0-1023)
            end_addr: Ending address (0-1023, must be >= start_addr)
        """
        print(f"\nMemory Dump from 0x{start_addr:03X} to 0x{end_addr:03X}:")
        print("Addr\tHex\tDec\tBin")
        print("-" * 40)
        
        for addr in range(start_addr, min(end_addr + 1, 1024)):
            bit_value = self.read_bit(addr)
            print(f"0x{addr:03X}\t{addr:03X}\t{addr:04d}\t{bit_value}")
    
    def bulk_test(self):
        """Run comprehensive tests on the SRAM"""
        print("=" * 50)
        print("Running Comprehensive SRAM Tests")
        print("=" * 50)
        
        results = {}
        
        # Test different patterns
        patterns = ["all_zeros", "all_ones", "alternating", "walking_one"]
        
        for pattern in patterns:
            results[pattern] = self.test_pattern(pattern)
            time.sleep(0.1)  # Short delay between tests
        
        # Summary
        print("\n" + "=" * 50)
        print("TEST SUMMARY")
        print("=" * 50)
        
        total_tests = 0
        total_passed = 0
        
        for pattern, result in results.items():
            total_tests += result["total"]
            total_passed += result["passed"]
            status = "PASS" if result["failed"] == 0 else "FAIL"
            print(f"{pattern:15} : {result['passed']:4d}/{result['total']:4d} - {status}")
        
        print("-" * 50)
        print(f"OVERALL        : {total_passed:4d}/{total_tests:4d}")
        
        if total_passed == total_tests:
            print("\nAll tests PASSED!")
        else:
            print(f"\n{total_tests - total_passed} tests FAILED")
        
        return results


def main():
    """
    Main function - configure your GPIO pins here
    Adjust these pin assignments based on your wiring!
    """
    # ============================================
    # CONFIGURE THESE PINS BASED ON YOUR WIRING!
    # ============================================
    
    # 10 address pins for A0-A9 (1024 addresses)
    # List your GPIO pins connected to A0 through A9
    ADDRESS_PINS = [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]  # Adjust these!
    
    # Data pin (I/O pin)
    DATA_PIN = 10  # Adjust this!
    
    # Control pins (active LOW)
    CE_PIN = 11  # Chip Enable
    WE_PIN = 12  # Write Enable  
    OE_PIN = 13  # Output Enable
    
    # ============================================
    
    # Initialize SRAM
    sram = AM9101_SRAM(ADDRESS_PINS, DATA_PIN, CE_PIN, WE_PIN, OE_PIN)
    
    try:
        # Run comprehensive tests
        sram.bulk_test()
        
        # Optional: Run individual tests
        # sram.test_pattern("all_zeros")
        # sram.test_pattern("all_ones")
        
        # Optional: Dump memory contents
        # sram.memory_dump(0, 63)
        
        # Optional: Manual read/write test
        # print("\nManual test:")
        # sram.write_bit(0x00, 1)  # Write 1 to address 0
        # print(f"Read from address 0: {sram.read_bit(0x00)}")
        # sram.write_bit(0x00, 0)  # Write 0 to address 0
        # print(f"Read from address 0: {sram.read_bit(0x00)}")
        
    except Exception as e:
        print(f"Error: {e}")
        print("\nCheck your wiring and pin assignments!")
        print("Make sure you've configured the GPIO pins correctly.")

if __name__ == "__main__":
    main()