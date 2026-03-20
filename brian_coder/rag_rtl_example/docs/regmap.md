# RAG RTL Example Register Map

This project uses AXI4-Lite as the transaction layer to interface with the RAG core.

| Address Offset | Name          | Access | Description                                      |
| :------------- | :------------ | :----- | :----------------------------------------------- |
| 0x00           | CTRL          | R/W    | Bit 0: Start lookup, Bit 1: Clear memory         |
| 0x04           | STATUS        | R      | Bit 0: Busy, Bit 1: Match found                  |
| 0x08           | QUERY_DATA    | W      | Input query data (32-bit key)                    |
| 0x0C           | RESULT_DATA   | R      | Output result data (32-bit value)                |
| 0x10-0x1F      | MEM_CTRL      | R/W    | Interface for loading the RAG database externally |

## Transaction Protocol
- **Interface**: AXI4-Lite (32-bit data, 12-bit address)
- **Clock**: Synchronous to `aclk`
- **Reset**: Active low `aresetn`
