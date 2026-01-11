SymbolShortcuts is a custom embedded hardware-software system designed to make entering mathematical and engineering symbols (π, Ω, ∫, µ, ∑, etc.) fast and intuitive. The project runs 
on an NXP FRDM-MCXN947 microcontroller using the uC/OS-III real-time operating system, where a menu-driven interface allows users to browse and select symbols using onboard buttons. 
The firmware handles timing, menu rendering, and symbol state management, while a host-side Python script receives the selected symbols and injects them into the computer as standard 
text input.

The system was developed as a senior capstone project to explore real-time embedded design, human-computer interaction, and hardware-software integration. It demonstrates task 
scheduling, inter-task communication, and deterministic timing on a resource-constrained microcontroller, as well as USB/serial data exchange with a desktop application. The goal is 
to provide a low-cost, extensible alternative to traditional keyboards for technical users who frequently work with specialized notation in mathematics, physics, and engineering.
