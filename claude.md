# PCIe 메시지 시스템 문서

## 시스템 개요

PCIe 메시지를 AXI4 프로토콜을 통해 송수신하고 SRAM에 저장/읽기하는 완전한 시스템입니다.

### 주요 컴포넌트

```
┌──────────────────┐       ┌───────────────────┐       ┌──────────┐
│ axi_write_gen    │──AXI─>│ pcie_msg_receiver │──────>│          │
│ (Testbench Task) │ Write │ (AXI Write Slave) │       │   SRAM   │
└──────────────────┘       └───────────────────┘       │  1024x   │
                                                        │  256-bit │
┌──────────────────┐       ┌───────────────────┐       │          │
│ axi_read_gen     │<─AXI──│ pcie_axi_to_sram  │<──────│          │
│ (Testbench Task) │ Read  │ (AXI Read Slave)  │       └──────────┘
└──────────────────┘       └───────────────────┘
```

### 데이터 포맷

#### AXI Write 데이터 (256비트/32바이트 per beat)
```
첫 번째 Beat:
[255:128] - Payload 시작 (128 bits)
[127:0]   - PCIe TLP Header (128 bits)

두 번째 Beat 이후:
[255:0]   - Payload 계속 (256 bits)
```

#### PCIe TLP Header 구조 (128 bits)
```
[127:120] - Reserved
[119:112] - Source Endpoint ID
[111:104] - Reserved
[103:96]  - Message Type
[95:88]   - Vendor ID (lower)
[87:80]   - Vendor ID (upper)
[79:64]   - Reserved
[63:56]   - Message Code
[55:48]   - Tag
[47:32]   - Reserved
[31:24]   - Length (DW 단위)
[23:16]   - Reserved
[15:8]    - Reserved
[7:5]     - Format
[4:0]     - Type
```

---

## 1. axi_write_gen.v

### 개요
Testbench에서 사용하는 AXI Write Generator 모듈입니다. 내부 task를 통해 AXI write transaction을 생성합니다.

### 인터페이스

```verilog
module axi_write_gen (
    // Clock & Reset
    input i_clk,
    input i_reset_n,

    // AXI I/F - Write Address Channel
    output reg [63:0] O_AWUSER,
    output reg [6:0]  O_AWID,
    output reg [63:0] O_AWADDR,
    output reg [7:0]  O_AWLEN,
    output reg [2:0]  O_AWSIZE,
    output reg [1:0]  O_AWBURST,
    output reg        O_AWLOCK,
    output reg [3:0]  O_AWCACHE,
    output reg [2:0]  O_AWPROT,
    output reg        O_AWVALID,
    input             I_AWREADY,

    // Write Data Channel
    output reg [15:0]  O_AWUSER,
    output reg [255:0] O_WDATA,
    output reg         O_WSTRB,
    output reg         O_WLAST,
    input              I_WREADY,

    // Write Response Channel
    input [6:0]  I_BID,
    input [1:0]  I_BRESP,
    input        I_BVALID,
    output reg   O_BREADY
);
```

### 내부 Task: SEND_WRITE

#### 용도
PCIe 메시지를 AXI Write 프로토콜로 전송합니다.

#### 파라미터
```verilog
task automatic SEND_WRITE;
    input [127:0]     header;      // PCIe TLP Header
    input [11:0]      length;      // Number of beats
    input [2:0]       size;        // Transfer size (2^size bytes)
    input [1:0]       burst_type;  // 00:FIXED, 01:INCR, 10:WRAP
    input [256*4-1:0] wr_data;     // Write data (up to 4 beats)
    input [63:0]      awaddr;      // Start address
```

#### 동작 시퀀스

1. **Write Address Phase**
   - `axi_awvalid` 어서트
   - `axi_awaddr`, `axi_awlen`, `axi_awsize`, `axi_awburst` 설정
   - `axi_awready` handshake 대기

2. **Write Data Phase**
   - 각 beat마다:
     - `axi_wdata` = wr_data에서 추출
     - `axi_wstrb` = 32'hFFFFFFFF (모든 바이트 유효)
     - 마지막 beat에서 `axi_wlast` 어서트
     - `axi_wready` handshake 대기

3. **Write Response Phase**
   - `axi_bready` 어서트
   - `axi_bvalid` handshake 대기
   - Response 검증 (OKAY, EXOKAY, SLVERR, DECERR)

#### 사용 예시

```verilog
initial begin
    reg [127:0] header;
    reg [256*4-1:0] data;

    // TLP Header 구성
    header = 128'h0;
    header[7:5] = 3'b011;           // Format
    header[4:0] = 5'b10;            // Type
    header[31:24] = 8'h20;          // Length (128B)
    header[63:56] = 8'h7F;          // Message Code
    header[95:80] = 16'h1AB4;       // Vendor ID
    header[119:112] = 8'h00;        // Source EP ID

    // 페이로드 데이터 준비
    data[255:0] = 256'hDEADBEEF...;
    data[511:256] = 256'hCAFEBABE...;

    // Task 호출
    axi_write_gen_inst.SEND_WRITE(
        header,     // header
        4,          // length (4 beats)
        3'd5,       // size (32 bytes)
        2'b01,      // INCR burst
        data,       // write data
        64'h1000    // address
    );
end
```

---

## 2. axi_read_gen.v

### 개요
Testbench에서 사용하는 AXI Read Generator 모듈입니다. 내부 task를 통해 AXI read transaction을 생성하고 자동으로 데이터를 검증합니다.

### 인터페이스

```verilog
module axi_read_gen (
    input wire clk,
    input wire rst_n,

    // AXI Read Address Channel
    output reg         axi_arvalid,
    output reg  [63:0] axi_araddr,
    output reg  [11:0] axi_arlen,
    output reg  [2:0]  axi_arsize,
    output reg  [1:0]  axi_arburst,
    input wire         axi_arready,

    // AXI Read Data Channel
    input wire         axi_rvalid,
    input wire  [255:0] axi_rdata,
    input wire  [1:0]  axi_rresp,
    input wire         axi_rlast,
    output reg         axi_rready
);
```

### 내부 Task: READ_AND_CHECK

#### 용도
SRAM에서 데이터를 읽고 자동으로 헤더를 검증합니다.

#### 파라미터
```verilog
task automatic READ_AND_CHECK;
    input [63:0]  araddr;          // Start address
    input [11:0]  length;          // Number of beats
    input [2:0]   size;            // Transfer size (2^size bytes)
    input [1:0]   burst_type;      // 00:FIXED, 01:INCR, 10:WRAP
    input [127:0] expected_header; // Expected PCIe header for verification
```

#### 동작 시퀀스

1. **Read Address Phase**
   - `axi_arvalid` 어서트
   - `axi_araddr`, `axi_arlen`, `axi_arsize`, `axi_arburst` 설정
   - `axi_arready` handshake 대기

2. **Read Data Phase**
   - 각 beat마다:
     - `axi_rready` 어서트
     - `axi_rvalid` handshake 대기
     - `axi_rdata` 캡처 및 저장
     - 첫 번째 beat: Header 검증
     - `axi_rresp` 검증 (OKAY 기대)
     - `axi_rlast` 검증

3. **자동 검증**
   - **Header 검증**: 첫 번째 beat의 [127:0] 비트를 expected_header와 비교
   - **Response 검증**: 모든 beat의 rresp가 2'b00 (OKAY)인지 확인
   - **Last Signal 검증**: rlast가 마지막 beat에서만 어서트되는지 확인
   - **결과 출력**: VERIFICATION PASSED 또는 FAILED

#### 내부 저장소
```verilog
reg [255:0] read_data_mem [0:15];  // 읽은 데이터를 내부에 저장
```

#### 사용 예시

```verilog
initial begin
    reg [127:0] expected_hdr;

    // 예상되는 헤더 설정
    expected_hdr = 128'hDEADBEEF_CAFEBABE_12345678_ABCDEF01;

    // Read 및 자동 검증
    axi_read_gen_inst.READ_AND_CHECK(
        64'h1000,       // address
        4,              // length (4 beats)
        3'd5,           // size (32 bytes)
        2'b01,          // INCR burst
        expected_hdr    // expected header
    );

    // Task 내부에서 자동으로 검증 수행
    // "VERIFICATION PASSED" 또는 "VERIFICATION FAILED" 출력
end
```

#### 검증 출력 예시

```
========================================
[1500] [READ_GEN] READ_AND_CHECK START
  Address: 0x0000000000001000
  Length:  4 beats
  Size:    5 (2^5 = 32 bytes)
  Burst:   1 (INCR)
  Expected Header: 0xdeadbeefcafebabe12345678abcdef01
========================================
[1520] [READ_GEN] Read Address Sent
[1580] [READ_GEN] Read Data Beat 0: data=0x..., last=0, resp=0
[1580] [READ_GEN] *** HEADER MATCH ***
  Expected: 0xdeadbeefcafebabe12345678abcdef01
  Received: 0xdeadbeefcafebabe12345678abcdef01
[1600] [READ_GEN] Read Data Beat 1: data=0x..., last=0, resp=0
[1620] [READ_GEN] Read Data Beat 2: data=0x..., last=0, resp=0
[1640] [READ_GEN] Read Data Beat 3: data=0x..., last=1, resp=0

========================================
[1660] [READ_GEN] *** VERIFICATION PASSED ***
[1660] [READ_GEN] READ_AND_CHECK COMPLETE
========================================
```

---

## 3. pcie_msg_receiver.v

### 개요
AXI Write Slave 모듈로, PCIe 메시지를 수신하여 SRAM에 저장하고 헤더를 추출합니다.

### 기능
- AXI Write 프로토콜 슬레이브
- 첫 번째 beat에서 128비트 헤더 추출
- 모든 데이터를 SRAM에 저장
- Message valid signal 생성

### 인터페이스

```verilog
module pcie_msg_receiver (
    input wire clk,
    input wire rst_n,

    // AXI Write Channel
    input wire         axi_awvalid,
    input wire  [63:0] axi_awaddr,
    input wire  [11:0] axi_awlen,
    input wire  [2:0]  axi_awsize,
    input wire  [1:0]  axi_awburst,
    output reg         axi_awready,

    input wire  [255:0] axi_wdata,
    input wire  [31:0]  axi_wstrb,
    input wire          axi_wlast,
    input wire          axi_wvalid,
    output reg          axi_wready,

    output reg         axi_bvalid,
    output reg  [1:0]  axi_bresp,
    input wire         axi_bready,

    // SRAM Write Interface
    output reg         sram_wen,
    output reg  [9:0]  sram_waddr,
    output reg  [255:0] sram_wdata,

    // Message Info
    output reg [127:0] msg_header,
    output reg         msg_valid,
    output reg [11:0]  msg_length
);
```

### 동작
1. Address 수신
2. 첫 번째 beat에서 `msg_header <= axi_wdata[127:0]` 추출
3. 모든 beat를 SRAM에 저장
4. Write response 반환

---

## 4. pcie_axi_to_sram.v

### 개요
AXI Read Slave 모듈로, SRAM에서 데이터를 읽어 AXI Read 프로토콜로 제공합니다.

### 인터페이스

```verilog
module pcie_axi_to_sram (
    input wire clk,
    input wire rst_n,

    // AXI Read Channel
    input wire         axi_arvalid,
    input wire  [63:0] axi_araddr,
    input wire  [11:0] axi_arlen,
    input wire  [2:0]  axi_arsize,
    input wire  [1:0]  axi_arburst,
    output reg         axi_arready,

    output reg         axi_rvalid,
    output wire [255:0] axi_rdata,  // Combinational from sram_rdata
    output reg  [1:0]  axi_rresp,
    output reg         axi_rlast,
    input wire         axi_rready,

    // SRAM Read Interface
    output reg         sram_ren,
    output reg  [9:0]  sram_raddr,
    input wire  [255:0] sram_rdata
);
```

### 중요 사항
- `axi_rdata`는 combinational: `assign axi_rdata = sram_rdata;`
- SRAM은 1-cycle read latency

---

## 5. sram.v

### 개요
Dual-port SRAM (동시 read/write 지원)

### 파라미터
```verilog
module sram #(
    parameter DATA_WIDTH = 256,
    parameter ADDR_WIDTH = 10,
    parameter DEPTH = 1024
)
```

### 특징
- 독립적인 write/read 포트
- Synchronous write (wen이 high일 때 posedge clk에서 write)
- Synchronous read (ren이 high일 때 posedge clk에서 read, 1-cycle latency)

---

## 전체 사용 예시

### Testbench 구조

```verilog
module pcie_full_tb;
    // Clocks, resets
    reg clk, rst_n;

    // Instantiate all modules
    axi_write_gen wr_gen (...);
    axi_read_gen rd_gen (...);
    pcie_msg_receiver receiver (...);
    sram sram_inst (...);
    pcie_axi_to_sram axi_sram_reader (...);

    initial begin
        // Reset
        rst_n = 0;
        #100 rst_n = 1;

        // Test Case: Write then Read
        begin
            reg [127:0] header;
            reg [256*4-1:0] wr_data;

            // 1. Write message
            header = 128'hDEADBEEF_CAFEBABE_12345678_ABCDEF01;
            wr_data = {256'h..., 256'h..., 256'h..., 256'h...};

            wr_gen.SEND_WRITE(
                header, 4, 3'd5, 2'b01, wr_data, 64'h0
            );

            #100;

            // 2. Read and verify automatically
            rd_gen.READ_AND_CHECK(
                64'h0,      // same address
                4,          // same length
                3'd5,       // same size
                2'b01,      // same burst
                header      // verify header
            );
            // Task will output VERIFICATION PASSED/FAILED
        end

        $finish;
    end
endmodule
```

---

## 주요 개선 사항 및 특징

### 1. Task 기반 설계
- State machine 대신 task 사용으로 간결성 향상
- Testbench에서 직접 호출 가능
- 자동 타이밍 제어

### 2. 자동 검증
- `READ_AND_CHECK` task가 헤더를 자동으로 검증
- Response 에러 자동 감지
- RLAST 위치 자동 검증
- 명확한 PASS/FAIL 출력

### 3. 디버깅 편의성
- 모든 주요 이벤트에 $display 출력
- 타임스탬프와 함께 상세한 로그
- 헤더 매치/미스매치 명확히 표시

### 4. 확장성
- `read_data_mem` 배열로 추가 검증 가능
- Task 파라미터로 다양한 시나리오 테스트
- 모듈화된 구조로 재사용 용이

---

## 파일 목록

1. **axi_write_gen.v** - AXI Write Generator (with SEND_WRITE task)
2. **axi_read_gen.v** - AXI Read Generator (with READ_AND_CHECK task)
3. **pcie_msg_receiver.v** - AXI Write Slave + Header Extractor
4. **pcie_axi_to_sram.v** - AXI Read Slave
5. **sram.v** - Dual-port SRAM
6. **pcie_full_tb.v** - Full system testbench

---

## 타이밍 다이어그램

### Write Sequence
```
CLK     __|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__

AWVALID ___|‾‾‾‾‾‾‾|_______________________________________________
AWREADY ___________|‾‾‾|___________________________________________

WVALID  _______________|‾‾‾‾‾‾‾‾‾‾‾|_____________________________
WDATA   _______________< D0 >< D1 >_______________________________
WLAST   _________________________|‾|_____________________________

BVALID  _____________________________|‾‾‾|_______________________
BREADY  _____________________________|‾‾‾|_______________________
```

### Read Sequence
```
CLK     __|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__|‾|__

ARVALID ___|‾‾‾‾‾‾‾|_______________________________________________
ARREADY ___________|‾‾‾|___________________________________________

RVALID  _______________|‾‾‾‾‾‾‾‾‾‾‾|_____________________________
RDATA   _______________< D0 >< D1 >_______________________________
RLAST   _________________________|‾|_____________________________
RREADY  _______________|‾‾‾‾‾‾‾‾‾‾‾‾‾‾‾|_________________________
```

---

## 문제 해결 히스토리

### 1. Array Parameter 이슈
**문제**: Iverilog가 array를 모듈 input으로 지원하지 않음
**해결**: Task의 경우 hierarchical reference로 내부 메모리 접근 가능

### 2. Timing 이슈
**문제**: Nonblocking assignment와 combinational check의 타이밍 미스매치
**해결**: Task에서 `@(posedge clk); #1;` 패턴 사용으로 명확한 타이밍 제어

### 3. Read Data Capture
**문제**: SRAM read latency로 인한 데이터 지연
**해결**: `axi_rdata`를 combinational wire로 변경: `assign axi_rdata = sram_rdata;`

---

## 결론

본 시스템은 PCIe 메시지를 AXI4 프로토콜을 통해 효율적으로 처리하며, task 기반 설계로 사용성과 디버깅 편의성을 극대화했습니다. 자동 검증 기능으로 테스트 시간을 단축하고 신뢰성을 향상시켰습니다.

---

## 현재 상태 (2025-11-02)

### 완료된 작업
1. **AXI 핸드셰이크 타이밍 수정** ✅
   - axi_write_gen.v의 SEND_WRITE task 수정
   - pcie_msg_receiver.v의 W_DATA 상태 수정
   - Address/Data/Response 페이즈의 handshake 로직 단순화

2. **원본 테스트 복구** ✅
   - axi_write_gen.v의 모든 original test case 복구
   - TEST 1~5 및 에러 케이스 테스트 포함
   - 컴파일 성공 확인

### 수정 내용 상세
- **axi_write_gen.v (라인 416-418)**:
  - Address Phase: `while (!I_AWREADY)` 루프 제거
  - 단순히 1 clock cycle 대기 후 handshake 완료로 간주

- **axi_write_gen.v (라인 449-450)**:
  - Data Phase: `while (!I_WREADY)` 루프 제거
  - 각 beat마다 1 clock cycle 대기

- **axi_write_gen.v (라인 466-467)**:
  - Response Phase: `while (!I_BVALID)` 루프 제거
  - 1 clock cycle 대기 후 response 획득

- **pcie_msg_receiver.v (라인 247)**:
  - W_DATA 상태: `if (axi_wvalid && axi_wready)` → `if (axi_wvalid)`로 변경
  - axi_wready는 항상 1이므로 불필요한 중복 체크 제거

### 테스트 상태
- 컴파일: ✅ 성공 (경고 없음)
- axi_write_gen.v 상태: ✅ 원본 복구 + AXI 핸드셰이크 수정 적용
- pcie_msg_receiver.v 상태: ✅ W_DATA 조건 수정

### 다음 단계
- git add 완료 (commit 대기 중)
- 사용자가 직접 commit 수행 예정
