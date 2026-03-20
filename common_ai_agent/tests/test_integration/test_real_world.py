"""
Real-world test: Common AI Agent에서 실제 사용하는 시나리오
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'common_ai_agent'))

from core.tools import write_file

print("=" * 60)
print("REAL-WORLD TEST: Common AI Agent Environment")
print("=" * 60)

# Test 1: Python 파일 작성 (에러 있음)
print("\n📝 Test 1: Python 파일 작성 (syntax error)")
print("-" * 60)
result = write_file(
    path="test_example.py",
    content='''def hello():
    print("Hello World)  # 따옴표 닫기 안함
    return 42
'''
)
print(result)

# Test 2: Verilog 파일 작성 (에러 있음)
print("\n📝 Test 2: Verilog 파일 작성 (syntax error)")
print("-" * 60)
result = write_file(
    path="test_counter.v",
    content='''module counter(
    input clk,
    input reset,
    output reg [7:0] count
);
    always @(posedge clk) begin
        if (reset)
            count <= 0;
        else
            count <= count + 1  // 세미콜론 빠짐
    end
endmodule
'''
)
print(result)

# Test 3: 정상적인 Python 파일
print("\n📝 Test 3: 정상적인 Python 파일")
print("-" * 60)
result = write_file(
    path="test_good.py",
    content='''def add(a, b):
    """두 수를 더합니다"""
    return a + b

def main():
    result = add(10, 20)
    print(f"Result: {result}")

if __name__ == "__main__":
    main()
'''
)
print(result)

# Test 4: 정상적인 Verilog 파일
print("\n📝 Test 4: 정상적인 Verilog 파일")
print("-" * 60)
result = write_file(
    path="test_good_counter.v",
    content='''module counter(
    input clk,
    input reset,
    output reg [7:0] count
);
    always @(posedge clk) begin
        if (reset)
            count <= 8'b0;
        else
            count <= count + 1'b1;
    end
endmodule
'''
)
print(result)

# Cleanup
print("\n🧹 Cleaning up test files...")
for f in ["test_example.py", "test_counter.v", "test_good.py", "test_good_counter.v"]:
    if os.path.exists(f):
        os.remove(f)
        print(f"   Removed {f}")

print("\n" + "=" * 60)
print("✅ Real-world test completed!")
print("=" * 60)
