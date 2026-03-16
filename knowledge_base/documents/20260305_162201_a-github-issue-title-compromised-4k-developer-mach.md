---
title: A GitHub Issue Title Compromised 4k Developer Machines
source: hacker_news
url: https://grith.ai/blog/clinejection-when-your-ai-tool-installs-another
points: 632
---

Title: A GitHub Issue Title Compromised 4k Developer Machines
Points: 632, Author: edf13, Comments: 196

My smart sleep mask broadcasts users' brainwaves to an open MQTT broker
I recently got a smart sleep mask from Kickstarter. I was not expecting to end up with the ability to read strangers' brainwaves and send them electric impulses in their sleep. But here we are.
The mask was from a small Chinese research company, very cool hardware -- EEG brain monitoring, electrical muscle stimulation around the eyes, vibration, heating, audio. The app was still rough around the edges though and the mask kept disconnecting, so I asked Claude to try reverse-engineer the Bluetooth protocol and build me a simple web control panel instead.
The first thing Claude did was scan for BLE (Bluetooth Low Energy) devices nearby. It found mine among 35 devices in range, connected, and mapped the interface -- two data channels. One for sending commands, one for streaming data.
Then it tried talking to it. Sent maybe a hundred different command patterns. Modbus frames, JSON, raw bytes, common headers. Unfortunately, the device said nothing back, the protocol was not a standard one.
So Claude went after the app instead. Grabbed the Android APK, decompiled it with jadx. Turns out the app is built with Flutter, which is a bit of a problem for reverse engineering. Flutter compiles Dart source code into native ARM64 machine code -- you can't just read it back like normal Java Android apps. The actual business logic lives in a 9MB binary blob.
But even compiled binaries have strings in them. Error messages, URLs, debug logs. Claude ran
on the binary and this was the most productive step of the whole session. Among the thousands of lines of Flutter framework noise, it found:
Hardcoded credentials for the company's message broker (shared by every copy of the app)
All fifteen command builder function names (e.g. to set vibration, heating, electric stimulation, etc.)
Protocol debug messages that revealed the packet structure -- header, direction byte, command type, payload, footer
We had the shape of the protocol. Still didn't have the actual byte values though.
, a tool specifically for decompiling Flutter's compiled Dart snapshots. It reconstructs the functions with readable annotations. Claude figured out the encoding, and just read off every command byte from every function. Fifteen commands, fully mapped.
Claude sent a six-byte query packet. The device came back with 153 bytes -- model number, firmware version, serial number, all eight sensor channel configurations (EEG at 250Hz, respiration, 3-axis accelerometer, 3-axis gyroscope). Battery at 83%.
Vibration control worked. Heating worked. EMS worked. Music worked. Claude built me a little web dashboard with sliders for everything. I was pretty happy with it.
That could have been the end of the story.
Remember the hardcoded credentials from earlier? While poking around, Claude tried using them to connect to the company's MQTT broker -- MQTT is a pub/sub messaging system standard in IoT, where devices publish sensor readings and 
