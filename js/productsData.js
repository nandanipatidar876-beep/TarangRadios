const TARANG_DATA = {
  categories: [
    {
      id: "development-boards",
      title: "Development Boards & Microcontrollers",
      shortTitle: "Dev Boards",
      tagline: "Arduino, ESP32, Raspberry Pi & Microcontroller Kits",
      icon: "cpu",
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      color: "#F2C94C",
      subcategories: [
        "Arduino Boards & Kits",
        "ESP32 & Wi-Fi / BLE Modules",
        "Raspberry Pi & Single Board Computers",
        "ARM & STM32 Microcontroller Boards"
      ]
    },
    {
      id: "sensors-modules",
      title: "Sensors & Sensor Modules",
      shortTitle: "Sensors",
      tagline: "Ultrasonic, IR, Motion, Temperature & Environmental Sensors",
      icon: "activity",
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      color: "#D14B14",
      subcategories: [
        "Temperature & Humidity Sensors (DHT11/DHT22)",
        "Ultrasonic & Distance Sensors (HC-SR04)",
        "IR & Motion Detection Sensors (PIR/Obstacle)",
        "Gas, Pressure & Biometric Sensor Modules"
      ]
    },
    {
      id: "electronic-modules-displays",
      title: "Electronic Modules & Displays",
      shortTitle: "Modules & Displays",
      tagline: "OLED, LCD, Relay Modules, Power Supply & Motor Drivers",
      icon: "monitor",
      image: "https://images.unsplash.com/photo-1550041473-d296a3a8a18a?auto=format&fit=crop&w=600&q=80",
      color: "#F2C94C",
      subcategories: [
        "0.96 inch OLED & 16x2 LCD Display Modules",
        "Relay Modules & Optocoupler Drivers",
        "DC Motor Drivers (L298N) & Stepper Modules",
        "Voltage Regulator & Buck-Boost Converter Modules"
      ]
    },
    {
      id: "iot-wireless",
      title: "IoT & Wireless Modules",
      shortTitle: "IoT & Wireless",
      tagline: "Wi-Fi, Bluetooth, LoRa, NRF24L01 & GSM/GPRS Modules",
      icon: "wifi",
      image: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=600&q=80",
      color: "#D14B14",
      subcategories: [
        "ESP8266 & ESP32 Wi-Fi Modules",
        "HC-05 & HC-06 Bluetooth Transceivers",
        "NRF24L01+ 2.4GHz RF Transceivers",
        "LoRa & SIM800L GSM/GPRS Modules"
      ]
    },
    {
      id: "gps-navigation",
      title: "GPS & Navigation Modules",
      shortTitle: "GPS & Navigation",
      tagline: "NEO-6M GPS, Magnetometer, Compass & Gyro Modules",
      icon: "compass",
      image: "https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=600&q=80",
      color: "#F2C94C",
      subcategories: [
        "NEO-6M / NEO-7M GPS Modules",
        "MPU-6050 6-Axis Gyro & Accelerometer",
        "HMC5883L 3-Axis Digital Compass",
        "Barometric & Altimeter Sensor Boards"
      ]
    },
    {
      id: "motors-drivers",
      title: "Motors & Motor Drivers",
      shortTitle: "Motors & Drivers",
      tagline: "Stepper Motors, Servo Motors, DC Gear Motors & Drivers",
      icon: "settings",
      image: "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=600&q=80",
      color: "#D14B14",
      subcategories: [
        "NEMA 17 Stepper Motors & A4988 Drivers",
        "SG90 & MG996R Servo Motors",
        "Dual H-Bridge Motor Drivers (L298N/L293D)",
        "BO Motors & Coreless Drone Motors"
      ]
    },
    {
      id: "batteries-power",
      title: "Batteries & Power Supplies",
      shortTitle: "Batteries & Power",
      tagline: "Lithium-ion Batteries, BMS Chargers, Buck/Boost & Adapters",
      icon: "battery-charging",
      image: "batteries and power/pixhawk-power-module.jpg",
      color: "#F2C94C",
      subcategories: [
        "Pixhawk Power Modules & BEC",
        "18650 Li-ion Cells & Battery Holders",
        "TP4056 Lithium Charging Modules & BMS",
        "LM2596 Step-Down & XL6009 Boost Converters",
        "SMPS Power Supplies & 12V Adapters",
        "Power Bank Modules & Voltage Regulators"
      ]
    },
    {
      id: "electronic-components",
      title: "Electronic Components",
      shortTitle: "Components",
      tagline: "Resistors, Capacitors, Diodes, Transistors, ICs & LEDs",
      icon: "cpu",
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      color: "#D14B14",
      subcategories: [
        "Resistor Kits & Potentiometers",
        "Ceramic & Electrolytic Capacitors",
        "Rectifier Diodes, Zener & LEDs",
        "NE555, LM358 & Logic Gate ICs"
      ]
    },
    {
      id: "connectors-terminals",
      title: "Connectors & Terminals",
      shortTitle: "Connectors",
      tagline: "JST, Berg Strip, Jumper Wires, DC Jacks & Terminal Blocks",
      icon: "link",
      image: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=600&q=80",
      color: "#F2C94C",
      subcategories: [
        "Male/Female Jumper Wire Cables",
        "JST XH, PH & SM Connector Sets",
        "2.54mm Pin Headers & Berg Strips",
        "Screw Terminal Blocks & DC Power Jacks"
      ]
    },
    {
      id: "switches-knobs",
      title: "Switches & Knobs",
      shortTitle: "Switches & Knobs",
      tagline: "Gillard Switches, Rocker Switches, Push Buttons & Rotary Knobs",
      icon: "toggle-right",
      image: "https://images.unsplash.com/photo-1550041473-d296a3a8a18a?auto=format&fit=crop&w=600&q=80",
      color: "#D14B14",
      subcategories: [
        "Gillard Industrial Toggle & Slide Switches",
        "Micro Tactile Push Buttons & Caps",
        "KCD1 Rocker & Rotary Band Switches",
        "Aluminum & Plastic Potentiometer Knobs"
      ]
    },
    {
      id: "class-d-audio",
      title: "Class D Audio Amplifier Boards",
      shortTitle: "Class D Audio",
      tagline: "CA-3166B 200W, PAM8403, TPA3116D2 & Bluetooth Amp Boards",
      icon: "volume-2",
      image: "class-d-audio/ca-3166b-bluetooth-amplifier.jpg",
      color: "#D14B14",
      subcategories: [
        "CA-3166B 2.1 Channel 200W Amp Boards",
        "PAM8403 2x3W Mini Digital Audio Boards",
        "TPA3116D2 2x50W / 100W Audio Amplifiers",
        "Bluetooth 5.0 Audio Receiver & Amp Boards",
        "TDA7498 2x100W High Power Class D Amplifiers",
        "Mono Subwoofer & 2.1 Channel Amp Modules"
      ]
    }
  ],

  brands: [
    { name: "Philips", logo: "📻 PHILIPS", desc: "Precision Electronic Components & Semiconductors" },
    { name: "Gillard", logo: "🔘 GILLARD", desc: "Industrial Grade Heavy Duty Switches & Control Gear" },
    { name: "Alcop", logo: "⚡ ALCOP", desc: "High Flexibility Industrial Cables & Wiring Harnesses" },
    { name: "Noel", logo: "🔥 NOEL", desc: "Professional Soldering Solutions, Wire & Flux" },
    { name: "Tarang", logo: "⚡ TARANG", desc: "Industrial Electronic Spare Parts & Microcontroller Modules" }
  ],

  products: [
    {
      id: "p1",
      name: "ESP32 Wi-Fi + Bluetooth Dual Core Development Board",
      categoryId: "development-boards",
      subcategory: "ESP32 & Wi-Fi / BLE Modules",
      brand: "Tarang",
      price: 450,
      badge: "Best Seller",
      rating: 4.9,
      reviews: 128,
      inStock: true,
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      description: "32-bit Dual-core ESP-WROOM-32 MCU board with built-in Wi-Fi, BLE, Micro-USB interface, and CP2102 driver for IoT projects.",
      specs: {
        "CPU": "32-bit Dual Core LX6 (240MHz)",
        "Wireless": "Wi-Fi 802.11 b/g/n + Bluetooth 4.2 BLE",
        "Flash Memory": "4MB QSPI Flash",
        "Pins": "38-Pin GPIO Header"
      }
    },
    {
      id: "p2",
      name: "Arduino UNO R3 Microcontroller Board",
      categoryId: "development-boards",
      subcategory: "Arduino Boards & Kits",
      brand: "Tarang",
      price: 550,
      badge: "Top Choice",
      rating: 4.8,
      reviews: 95,
      inStock: true,
      image: "https://images.unsplash.com/photo-1553406830-ef2513450d76?auto=format&fit=crop&w=600&q=80",
      description: "ATmega328P based microcontroller board with 14 digital I/O pins, 6 analog inputs, 16 MHz quartz crystal, and USB cable included.",
      specs: {
        "Microcontroller": "ATmega328P",
        "Operating Voltage": "5V",
        "Digital I/O Pins": "14 (6 PWM outputs)",
        "Clock Speed": "16 MHz"
      }
    },
    {
      id: "p3",
      name: "HC-SR04 Ultrasonic Distance Sensor Module",
      categoryId: "sensors-modules",
      subcategory: "Ultrasonic & Distance Sensors (HC-SR04)",
      brand: "Tarang",
      price: 120,
      badge: "High Accuracy",
      rating: 4.9,
      reviews: 88,
      inStock: true,
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      description: "Non-contact ultrasonic range detection module measuring 2cm to 400cm with high accuracy and stable reading capability.",
      specs: {
        "Working Voltage": "DC 5V",
        "Ranging Distance": "2cm - 400cm",
        "Resolution": "0.3cm",
        "Measuring Angle": "15 Degree"
      }
    },
    {
      id: "p4",
      name: "DHT11 Temperature & Humidity Sensor Module",
      categoryId: "sensors-modules",
      subcategory: "Temperature & Humidity Sensors (DHT11/DHT22)",
      brand: "Tarang",
      price: 95,
      badge: "Essential Sensor",
      rating: 4.8,
      reviews: 142,
      inStock: true,
      image: "https://images.unsplash.com/photo-1550041473-d296a3a8a18a?auto=format&fit=crop&w=600&q=80",
      description: "Calibrated digital signal output temperature and humidity composite sensor for weather station and environmental monitoring.",
      specs: {
        "Humidity Range": "20% - 90% RH",
        "Temperature Range": "0 - 50°C",
        "Signal Output": "Digital Single-Bus",
        "Operating Voltage": "3.3V - 5.5V"
      }
    },
    {
      id: "p5",
      name: "0.96 inch I2C OLED Display Module (128x64)",
      categoryId: "electronic-modules-displays",
      subcategory: "0.96 inch OLED & 16x2 LCD Display Modules",
      brand: "Tarang",
      price: 280,
      badge: "High Contrast",
      rating: 4.9,
      reviews: 110,
      inStock: true,
      image: "https://images.unsplash.com/photo-1550041473-d296a3a8a18a?auto=format&fit=crop&w=600&q=80",
      description: "Self-luminous 128x64 OLED graphic screen module with SSD1306 driver chip and 4-pin I2C communication interface.",
      specs: {
        "Resolution": "128 x 64 Pixels",
        "Driver IC": "SSD1306",
        "Interface": "I2C (VCC, GND, SCL, SDA)",
        "Operating Voltage": "3.3V - 5V"
      }
    },
    {
      id: "p6",
      name: "NRF24L01+ 2.4GHz RF Wireless Transceiver Module",
      categoryId: "iot-wireless",
      subcategory: "NRF24L01+ 2.4GHz RF Transceivers",
      brand: "Tarang",
      price: 130,
      badge: "Wireless IoT",
      rating: 4.9,
      reviews: 154,
      inStock: true,
      image: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=600&q=80",
      description: "Ultra low power 2.4GHz ISM band wireless transceiver module with SPI interface for long range microcontroller data communication.",
      specs: {
        "Frequency Band": "2.4GHz ISM",
        "Data Rate": "2Mbps / 1Mbps / 250Kbps",
        "Operating Voltage": "1.9V - 3.6V",
        "Interface": "SPI"
      }
    },
    {
      id: "p7",
      name: "GY-NEO6MV2 GPS Module with Onboard Antenna",
      categoryId: "gps-navigation",
      subcategory: "NEO-6M / NEO-7M GPS Modules",
      brand: "Tarang",
      price: 680,
      badge: "Precision GPS",
      rating: 4.8,
      reviews: 92,
      inStock: true,
      image: "https://images.unsplash.com/photo-1524661135-423995f22d0b?auto=format&fit=crop&w=600&q=80",
      description: "High-sensitivity GPS positioning module with ceramic patch antenna, EEPROM memory, and UART TTL serial interface.",
      specs: {
        "Baud Rate": "9600 bps Default",
        "EEPROM": "Built-in Configuration Backup",
        "Interface": "UART TTL",
        "Supply Voltage": "3V - 5V"
      }
    },
    {
      id: "p8",
      name: "NEMA 17 Bipolar Stepper Motor (1.7A 40Ncm)",
      categoryId: "motors-drivers",
      subcategory: "NEMA 17 Stepper Motors & A4988 Drivers",
      brand: "Tarang",
      price: 850,
      badge: "High Torque",
      rating: 4.9,
      reviews: 75,
      inStock: true,
      image: "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=600&q=80",
      description: "High torque 1.8 degree bipolar NEMA 17 stepper motor ideal for 3D printers, CNC machines, and robotics projects.",
      specs: {
        "Step Angle": "1.8 Degree",
        "Holding Torque": "40 Ncm",
        "Rated Current": "1.7A per Phase",
        "Phases": "2-Phase Bipolar"
      }
    },
    {
      id: "p9",
      name: "L298N Dual H-Bridge DC Motor Driver Module",
      categoryId: "motors-drivers",
      subcategory: "Dual H-Bridge Motor Drivers (L298N/L293D)",
      brand: "Tarang",
      price: 180,
      badge: "High Power",
      rating: 4.8,
      reviews: 76,
      inStock: true,
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      description: "High voltage dual H-bridge motor driver module capable of driving two DC motors or one 4-wire two-phase stepper motor.",
      specs: {
        "Driver Chip": "L298N Dual H-Bridge",
        "Drive Voltage": "5V - 35V",
        "Peak Current": "2A per Bridge",
        "Logic Voltage": "5V"
      }
    },
    {
      id: "p_pixhawk_pm",
      name: "Pixhawk Flight Controller Power Module V1.0 (XT60 Plug)",
      categoryId: "batteries-power",
      subcategory: "Pixhawk Power Modules & BEC",
      brand: "Tarang",
      price: 650,
      badge: "Drone Power",
      rating: 5.0,
      reviews: 98,
      inStock: true,
      image: "batteries and power/pixhawk-power-module.jpg",
      description: "APM / Pixhawk Flight Controller Power Module V1.0 with 5.3V BEC output and current/voltage sensing via XT60 connectors for drone power management.",
      specs: {
        "Max Input Voltage": "30V (6S LiPo)",
        "Max Current Sensing": "90A",
        "BEC Output": "5.3V / 2.25A DC-DC",
        "Connectors": "XT60 Male / Female & 6-Pin Cable"
      }
    },
    {
      id: "p10",
      name: "TP4056 1A Li-ion Battery Charger Module with Protection",
      categoryId: "batteries-power",
      subcategory: "TP4056 Lithium Charging Modules & BMS",
      brand: "Tarang",
      price: 45,
      badge: "Must Have",
      rating: 4.9,
      reviews: 210,
      inStock: true,
      image: "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?auto=format&fit=crop&w=600&q=80",
      description: "Type-C USB 1A linear lithium battery charger board with DW01 over-charge and over-discharge protection circuit.",
      specs: {
        "Input Interface": "Type-C USB / Soldering Pads",
        "Max Charging Current": "1000 mA (1A)",
        "Charge Cut-Off Voltage": "4.2V +/- 1%",
        "Protection": "Over-charge / Over-discharge / Over-current"
      }
    },
    {
      id: "p10_1",
      name: "3.7V 2600mAh 18650 Rechargeable Li-ion Battery Cell",
      categoryId: "batteries-power",
      subcategory: "18650 Li-ion Cells & Battery Holders",
      brand: "Tarang",
      price: 180,
      badge: "High Capacity",
      rating: 4.9,
      reviews: 312,
      inStock: true,
      image: "https://images.unsplash.com/photo-1619642751034-765dfdf7c58e?auto=format&fit=crop&w=600&q=80",
      description: "High performance 3.7V 2600mAh flat-top 18650 lithium-ion cell for power banks, drones, and DIY battery packs.",
      specs: {
        "Nominal Voltage": "3.7V",
        "Capacity": "2600 mAh",
        "Cell Type": "Flat Top 18650",
        "Discharge Current": "5A Continuous"
      }
    },
    {
      id: "p10_2",
      name: "2-Slot 18650 Battery Holder Enclosure Box with Wire Leads",
      categoryId: "batteries-power",
      subcategory: "18650 Li-ion Cells & Battery Holders",
      brand: "Tarang",
      price: 35,
      badge: "Essential",
      rating: 4.8,
      reviews: 145,
      inStock: true,
      image: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=600&q=80",
      description: "Durable ABS plastic 2x 18650 battery case container with 15cm color coded wire leads for series connection.",
      specs: {
        "Slot Count": "2 Cells (7.4V Series Output)",
        "Material": "Impact Resistant ABS",
        "Lead Length": "150mm Red/Black Wires",
        "Mounting": "Built-in Screw Holes"
      }
    },
    {
      id: "p10_3",
      name: "3S 20A 12.6V 18650 Lithium Battery BMS Protection Board",
      categoryId: "batteries-power",
      subcategory: "TP4056 Lithium Charging Modules & BMS",
      brand: "Tarang",
      price: 95,
      badge: "BMS Protection",
      rating: 4.9,
      reviews: 188,
      inStock: true,
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      description: "3 Series 20A continuous discharge BMS board with automatic short circuit and overcharge protection for 12V Li-ion battery packs.",
      specs: {
        "Voltage Rating": "12.6V Max Charge",
        "Continuous Current": "20A",
        "Overcharge Protection": "4.25V ± 0.05V",
        "Overdischarge Protection": "2.5V ± 0.08V"
      }
    },
    {
      id: "p10_4",
      name: "LM2596 DC-DC Step-Down Buck Converter Module 3A",
      categoryId: "batteries-power",
      subcategory: "LM2596 Step-Down & XL6009 Boost Converters",
      brand: "Tarang",
      price: 85,
      badge: "Top Efficiency",
      rating: 4.9,
      reviews: 240,
      inStock: true,
      image: "https://images.unsplash.com/photo-1550041473-d296a3a8a18a?auto=format&fit=crop&w=600&q=80",
      description: "High-efficiency 3A DC step-down voltage regulator module with adjustable potentiometer (Input: 4V-35V, Output: 1.23V-30V).",
      specs: {
        "Input Voltage": "4V - 35V DC",
        "Output Voltage": "1.23V - 30V DC (Adjustable)",
        "Output Current": "3A Max (with heatsink)",
        "Conversion Efficiency": "Up to 92%"
      }
    },
    {
      id: "p10_5",
      name: "XL6009 4A DC-DC High-Frequency Step-Up Boost Module",
      categoryId: "batteries-power",
      subcategory: "LM2596 Step-Down & XL6009 Boost Converters",
      brand: "Tarang",
      price: 95,
      badge: "Boost Converter",
      rating: 4.8,
      reviews: 175,
      inStock: true,
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      description: "400KHz 4A high efficiency DC-DC step-up voltage converter module turning low battery voltage (3V-32V) up to 5V-35V.",
      specs: {
        "Input Range": "3V - 32V DC",
        "Output Range": "5V - 35V DC (Adjustable)",
        "Switching Frequency": "400 KHz",
        "Max Output Current": "4A"
      }
    },
    {
      id: "p10_6",
      name: "12V 5A 60W Industrial Metal Clad SMPS Power Supply",
      categoryId: "batteries-power",
      subcategory: "SMPS Power Supplies & 12V Adapters",
      brand: "Tarang",
      price: 450,
      badge: "Industrial Grade",
      rating: 4.9,
      reviews: 130,
      inStock: true,
      image: "https://images.unsplash.com/photo-1581092160607-ee22621dd758?auto=format&fit=crop&w=600&q=80",
      description: "Heavy duty honeycomb aluminum enclosure 12V 5A regulated switching power supply with overload and surge protection.",
      specs: {
        "Input Voltage": "110V / 220V AC",
        "Output Voltage": "12V DC ± 5%",
        "Output Current": "5 Ampere (60W Power)",
        "Protection": "Short Circuit / Overload / Over Voltage"
      }
    },
    {
      id: "p10_7",
      name: "12V 2A DC Power Adapter with 5.5x2.1mm Output Jack",
      categoryId: "batteries-power",
      subcategory: "SMPS Power Supplies & 12V Adapters",
      brand: "Tarang",
      price: 180,
      badge: "Plug & Play",
      rating: 4.8,
      reviews: 215,
      inStock: true,
      image: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=600&q=80",
      description: "Regulated AC 100-240V to DC 12V 2000mA wall power supply adapter with standard center-positive 5.5x2.1mm DC barrel connector.",
      specs: {
        "Input": "AC 100V - 240V 50/60Hz",
        "Output": "DC 12V 2A (24W)",
        "Connector": "5.5mm x 2.1mm Barrel Plug",
        "Cable Length": "1.2 Meter"
      }
    },
    {
      id: "p10_8",
      name: "Dual USB 5V 2.4A LCD Power Bank Charger Controller Module",
      categoryId: "batteries-power",
      subcategory: "Power Bank Modules & Voltage Regulators",
      brand: "Tarang",
      price: 140,
      badge: "Smart Display",
      rating: 4.9,
      reviews: 190,
      inStock: true,
      image: "https://images.unsplash.com/photo-1550041473-d296a3a8a18a?auto=format&fit=crop&w=600&q=80",
      description: "Dual USB output step-up module with blue backlit LCD screen showing real-time battery percentage and charging status.",
      specs: {
        "Input Interface": "Micro USB / Type-C 5V 2.1A",
        "Dual Output": "USB 5V 1A & 5V 2.4A",
        "Display": "Backlit LCD Battery % Indicator",
        "LED Torch": "Built-in Emergency LED"
      }
    },
    {
      id: "p10_9",
      name: "AMS1117 3.3V Step-Down Voltage Regulator Power Supply Module",
      categoryId: "batteries-power",
      subcategory: "Power Bank Modules & Voltage Regulators",
      brand: "Tarang",
      price: 30,
      badge: "Precision LDO",
      rating: 4.8,
      reviews: 260,
      inStock: true,
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      description: "Compact 800mA low dropout (LDO) voltage regulator module stepping down 4.75V-12V to steady 3.3V DC for sensors and microcontrollers.",
      specs: {
        "Input Voltage": "DC 4.75V - 12V",
        "Output Voltage": "3.3V DC (Fixed ± 1%)",
        "Max Current": "800 mA",
        "Indicator": "Onboard Power LED"
      }
    },
    {
      id: "p11",
      name: "600 Pcs 1/4W Metal Film Resistor Assortment Kit (30 Values)",
      categoryId: "electronic-components",
      subcategory: "Resistor Kits & Potentiometers",
      brand: "Tarang",
      price: 320,
      badge: "Value Pack",
      rating: 5.0,
      reviews: 180,
      inStock: true,
      image: "https://images.unsplash.com/photo-1518770660439-4636190af475?auto=format&fit=crop&w=600&q=80",
      description: "High precision 1% 1/4W metal film resistor kit containing 20 pieces each of 30 standard resistance values from 10 Ohm to 1M Ohm.",
      specs: {
        "Tolerance": "±1% Metal Film",
        "Power Rating": "0.25W (1/4 Watt)",
        "Values": "30 Standard Resistance Values",
        "Total Quantity": "600 Pieces"
      }
    },
    {
      id: "p12",
      name: "120 Pcs Jumper Wire Ribbon Cable Kit (M-M, M-F, F-F)",
      categoryId: "connectors-terminals",
      subcategory: "Male/Female Jumper Wire Cables",
      brand: "Tarang",
      price: 240,
      badge: "Prototyping Kit",
      rating: 4.9,
      reviews: 165,
      inStock: true,
      image: "https://images.unsplash.com/photo-1544197150-b99a580bb7a8?auto=format&fit=crop&w=600&q=80",
      description: "20cm 40-pin ribbon jumper cables set includes Male to Male, Male to Female, and Female to Female wires for breadboard prototyping.",
      specs: {
        "Wire Length": "20 cm",
        "Pitch": "2.54mm Pin Header Compatible",
        "Wire Gauge": "28 AWG Multi-color",
        "Quantity": "3 Bundles x 40 Pins (120 Total Wires)"
      }
    },
    {
      id: "p13",
      name: "Gillard Heavy Duty Industrial Toggle Switch (15A 250V)",
      categoryId: "switches-knobs",
      subcategory: "Gillard Industrial Toggle & Slide Switches",
      brand: "Gillard",
      price: 150,
      badge: "Heavy Duty",
      rating: 5.0,
      reviews: 98,
      inStock: true,
      image: "https://images.unsplash.com/photo-1550041473-d296a3a8a18a?auto=format&fit=crop&w=600&q=80",
      description: "Original Gillard SPST/DPDT heavy duty metal bat handle toggle switch rated for 15A 250VAC industrial electrical applications.",
      specs: {
        "Brand": "Gillard Switches",
        "Current Rating": "15A 250VAC / 20A 125VAC",
        "Contact Material": "Silver Alloy",
        "Mounting Hole": "12mm Diameter"
      }
    },
    {
      id: "p_ca3166b",
      name: "Tarang CA-3166B 2.1 Channel 200W Bluetooth Power Amplifier Board",
      categoryId: "class-d-audio",
      subcategory: "CA-3166B 2.1 Channel 200W Amp Boards",
      brand: "Tarang",
      price: 680,
      badge: "200W Output",
      rating: 5.0,
      reviews: 145,
      inStock: true,
      image: "class-d-audio/ca-3166b-bluetooth-amplifier.jpg",
      description: "Tarang CA-3166B 2.1 Channel (50W L + 50W R + 100W Subwoofer) 200W Total Bluetooth 5.0 & AUX Power Amplifier Board with 3 Metal Control Knobs.",
      specs: {
        "Model": "CA-3166B",
        "Power Output": "200W Total (50W Left + 50W Right + 100W Subwoofer)",
        "Working Voltage": "DC 9V - 24V (12V/24V Recommended)",
        "Audio Input": "Bluetooth 5.0 & 3.5mm AUX Input",
        "Impedance": "4Ω - 8Ω",
        "Package Content": "1x 2.1 Ch Board + 3x Silver Knobs + Wires"
      }
    },
    {
      id: "p_class_d_1",
      name: "PAM8403 2x3W Mini Class D Digital Audio Amplifier Board",
      categoryId: "class-d-audio",
      subcategory: "PAM8403 2x3W Mini Digital Audio Boards",
      brand: "Tarang",
      price: 40,
      badge: "Mini Amp",
      rating: 4.9,
      reviews: 320,
      inStock: true,
      image: "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=600&q=80",
      description: "Miniature 2-channel 3W+3W Class D digital audio amplifier module operating on 2.5V-5V DC with ultra-low noise and high efficiency (>90%).",
      specs: {
        "Power Output": "3W + 3W (4 Ohm Speakers)",
        "Operating Voltage": "2.5V - 5.5V DC (USB Powered)",
        "Efficiency": "Over 90%",
        "Dimensions": "21mm x 18mm"
      }
    },
    {
      id: "p_class_d_2",
      name: "TPA3116D2 Dual Channel 2x50W Class D Stereo Audio Amplifier",
      categoryId: "class-d-audio",
      subcategory: "TPA3116D2 2x50W / 100W Audio Amplifiers",
      brand: "Tarang",
      price: 340,
      badge: "High Power",
      rating: 4.9,
      reviews: 215,
      inStock: true,
      image: "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80",
      description: "TPA3116D2 high power digital Class D audio power amplifier board delivering 50W per channel clean audio output with onboard aluminum heatsink.",
      specs: {
        "Output Power": "50W + 50W RMS",
        "Supply Voltage": "DC 4.5V - 26V (24V Recommended)",
        "SNR": "100dB",
        "Channel": "Dual Channel Stereo"
      }
    },
    {
      id: "p_class_d_3",
      name: "Bluetooth 5.0 Audio Amplifier Board 2x50W with AUX Input",
      categoryId: "class-d-audio",
      subcategory: "Bluetooth 5.0 Audio Receiver & Amp Boards",
      brand: "Tarang",
      price: 420,
      badge: "Bluetooth 5.0",
      rating: 5.0,
      reviews: 180,
      inStock: true,
      image: "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=600&q=80",
      description: "Dual 50W Bluetooth 5.0 wireless audio receiver & amplifier board with 3.5mm AUX input jack, volume potentiometer, and acrylic protective shell.",
      specs: {
        "Bluetooth Version": "Bluetooth 5.0 (15m Range)",
        "Output Power": "50W x 2 Channels",
        "Input Modes": "Bluetooth / 3.5mm AUX Input",
        "Supply Voltage": "DC 9V - 24V"
      }
    },
    {
      id: "p_class_d_4",
      name: "TDA7498 2x100W Heavy Duty Dual BTL Class D Audio Amplifier",
      categoryId: "class-d-audio",
      subcategory: "TDA7498 2x100W High Power Class D Amplifiers",
      brand: "Tarang",
      price: 780,
      badge: "Heavy Duty 200W",
      rating: 4.8,
      reviews: 95,
      inStock: true,
      image: "https://images.unsplash.com/photo-1511671782779-c97d3d27a1d4?auto=format&fit=crop&w=600&q=80",
      description: "Dual BTL TDA7498 100W+100W Class-D audio amplifier board for home theatre, DJ speakers, and heavy duty audio projects.",
      specs: {
        "Max Output": "100W + 100W RMS (4 Ohm)",
        "Operating Voltage": "DC 14V - 39V",
        "Efficiency": "88%",
        "Protection": "Short-circuit & Over-temperature"
      }
    },
    {
      id: "p_class_d_5",
      name: "TPA3116D2 2.1 Channel 50W+50W+100W Subwoofer Amplifier Board",
      categoryId: "class-d-audio",
      subcategory: "Mono Subwoofer & 2.1 Channel Amp Modules",
      brand: "Tarang",
      price: 650,
      badge: "2.1 Subwoofer",
      rating: 4.9,
      reviews: 140,
      inStock: true,
      image: "https://images.unsplash.com/photo-1545454675-3531b543be5d?auto=format&fit=crop&w=600&q=80",
      description: "2.1 Channel Class D audio amplifier board with dedicated 100W subwoofer output and 50W left/right stereo channels with bass & treble control knobs.",
      specs: {
        "Output Channels": "50W Left + 50W Right + 100W Subwoofer",
        "Power Supply": "DC 12V - 24V (5A+ Recommended)",
        "Controls": "Volume / Subwoofer Frequency / Treble / Bass",
        "Impedance": "4 - 8 Ohm"
      }
    }
  ]
};

