"""
测试流式输出是否正常工作
直接调用 LangGraph API 并打印所有收到的事件
"""
import httpx
import json
import uuid

API_URL = "http://127.0.0.1:8123"
GRAPH_ID = "progressive_skill_generation"  # 使用 graph ID

def test_stream():
    print("1. 创建 thread...")
    
    # 先创建 thread
    with httpx.Client() as client:
        resp = client.post(
            f"{API_URL}/threads",
            json={}  # 空 body
        )
        print(f"   Create thread response: {resp.status_code}")
        if resp.status_code == 200:
            thread_data = resp.json()
            thread_id = thread_data.get("thread_id")
            print(f"   Thread ID: {thread_id}")
        else:
            print(f"   Response: {resp.text}")
            # 尝试不同的方式
            thread_id = str(uuid.uuid4())
            print(f"   Using random thread ID: {thread_id}")

    # 2. 发送流式请求
    print("\n2. 发送流式请求...")
    print("=" * 60)
    
    # LangGraph API 格式
    payload = {
        "assistant_id": GRAPH_ID,
        "input": {
            "requirement": "生成一个简单的火球术技能",
            "messages": [
                {"type": "human", "content": "生成一个简单的火球术技能"}
            ]
        },
        "stream_mode": ["values", "custom"]
    }
    
    event_count = 0
    custom_event_count = 0
    
    print(f"请求 URL: {API_URL}/threads/{thread_id}/runs/stream")
    print(f"Graph ID: {GRAPH_ID}")
    print("=" * 60)
    
    try:
        with httpx.Client(timeout=300) as client:
            with client.stream(
                "POST",
                f"{API_URL}/threads/{thread_id}/runs/stream",
                json=payload,
                params={"graph_id": GRAPH_ID}  # 通过 query param 指定 graph
            ) as response:
                print(f"Response status: {response.status_code}")
                
                if response.status_code != 200:
                    print(f"Error: {response.read().decode()}")
                    return
                
                buffer = ""
                for chunk in response.iter_text():
                    buffer += chunk
                    
                    # 解析 SSE 事件
                    while "\n\n" in buffer:
                        event_str, buffer = buffer.split("\n\n", 1)
                        
                        # 解析事件类型和数据
                        event_type = None
                        event_data = None
                        
                        for line in event_str.split("\n"):
                            if line.startswith("event:"):
                                event_type = line[6:].strip()
                            elif line.startswith("data:"):
                                try:
                                    event_data = json.loads(line[5:].strip())
                                except:
                                    event_data = line[5:].strip()
                        
                        if event_type:
                            event_count += 1
                            
                            if event_type == "custom":
                                custom_event_count += 1
                                # 打印 custom 事件详情
                                if isinstance(event_data, dict):
                                    evt_type = event_data.get("type", "unknown")
                                    chunk_preview = str(event_data.get("chunk", ""))[:50]
                                    print(f"🔥 [CUSTOM #{custom_event_count}] type={evt_type}, chunk={chunk_preview}...")
                                else:
                                    print(f"🔥 [CUSTOM #{custom_event_count}] {event_data}")
                            elif event_type == "values":
                                # 只打印简要信息
                                if isinstance(event_data, dict):
                                    keys = list(event_data.keys())[:5]
                                    msg_count = len(event_data.get("messages", []))
                                    print(f"📦 [VALUES #{event_count}] keys={keys}, messages={msg_count}")
                            elif event_type == "end":
                                print(f"✅ [END] Stream completed")
                            elif event_type == "error":
                                print(f"❌ [ERROR] {event_data}")
                            else:
                                print(f"📨 [{event_type.upper()}] {str(event_data)[:100]}...")
    except Exception as e:
        print(f"Exception: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print(f"总计: {event_count} 个事件, 其中 {custom_event_count} 个 custom 事件")
    
    if custom_event_count == 0:
        print("\n⚠️  没有收到 custom 事件！这说明 StreamWriter 没有正确工作。")
    else:
        print("\n✅ 收到了 custom 事件，流式输出正常工作！")

if __name__ == "__main__":
    test_stream()
