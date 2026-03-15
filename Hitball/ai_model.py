# ai_model.py
import torch
import torch.nn as nn
import torch.optim as optim
import random

class PongAI(nn.Module):
    """
    3层 MLP (多层感知机) 神经网络模型
    输入层: 6维特征 (球x, 球y, 球vx, 球vy, 玩家挡板y, AI挡板y)
    隐藏层: 128维
    输出层: 2维 (向上移动的概率分布, 向下移动的概率分布)
    """
    def __init__(self):
        super(PongAI, self).__init__()
        self.net = nn.Sequential(
            nn.Linear(6, 128),
            nn.ReLU(),
            nn.Linear(128, 128),
            nn.ReLU(),
            nn.Linear(128, 2)  # 输出动作: 0 (Up), 1 (Down)
        )

    def forward(self, x):
        return self.net(x)

    def predict(self, state):
        """
        根据当前状态预测动作
        :param state:[bx, by, bvx, bvy, player_y, ai_y] (归一化后的数据)
        :return: 0 (向上) 或 1 (向下)
        """
        self.eval() # 切换到评估模式
        with torch.no_grad():
            state_tensor = torch.tensor(state, dtype=torch.float32).unsqueeze(0)
            logits = self(state_tensor)
            # 使用 argmax 选择概率最大的动作
            action = torch.argmax(logits, dim=1).item()
        return action

def train_initial_model():
    """
    非常 Geek 的设计：每次启动前生成模拟数据快速预训练！
    这样项目无需附带 .pth 权重文件，也能开箱即用，并证明模型是真的在做推理。
    """
    print(" [人机 初始化中] 正在生成模拟数据并预训练 PyTorch 模型，请稍候...")
    model = PongAI()
    optimizer = optim.Adam(model.parameters(), lr=0.01)
    criterion = nn.CrossEntropyLoss()

    X_train =[]
    Y_train =[]

    # 1. 生成 5000 条带有简单物理规律的合成数据
    for _ in range(5000):
        bx = random.random()
        by = random.random()
        bvx = random.uniform(-1, 1)
        bvy = random.uniform(-1, 1)
        player_y = random.random()
        ai_y = random.random()

        # 简单的启发式预测：球的落点趋势
        # 如果球向右飞 (bvx > 0)，预测落点；否则默认居中防守
        if bvx > 0:
            predicted_y = by + bvy * (1.0 - bx) 
        else:
            predicted_y = 0.5
        
        # 限制范围
        predicted_y = max(0.0, min(1.0, predicted_y))

        # 根据预测落点决定动作：0 (Up) / 1 (Down)
        action = 0 if predicted_y < ai_y else 1

        X_train.append([bx, by, bvx, bvy, player_y, ai_y])
        Y_train.append(action)

    X_tensor = torch.tensor(X_train, dtype=torch.float32)
    Y_tensor = torch.tensor(Y_train, dtype=torch.long)

    # 2. 快速训练 100 个 Epoch
    model.train()
    for epoch in range(100):
        optimizer.zero_grad()
        outputs = model(X_tensor)
        loss = criterion(outputs, Y_tensor)
        loss.backward()
        optimizer.step()

    print(f" [人机 初始化完成] 模型已掌握基本击球策略！最后的 Loss: {loss.item():.4f}")
    return model

if __name__ == "__main__":
    # 测试一下模型构建
    test_model = train_initial_model()
    dummy_state =[0.5, 0.5, 0.5, 0.1, 0.5, 0.5]
    print(f"测试预测结果: {test_model.predict(dummy_state)}")