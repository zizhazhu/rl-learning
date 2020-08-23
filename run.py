import gym
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F


class Net(torch.nn.Module):

    def __init__(self):
        super(Net, self).__init__()
        self.action_embed = torch.nn.Embedding(2, 64)
        self.state_trans = torch.nn.Linear(4, 64)
        self.fc2 = torch.nn.Linear(128, 128)
        self.fc3 = torch.nn.Linear(128, 1)

    def forward(self, s, a):
        s = torch.tensor(s, dtype=torch.float)
        a = torch.tensor(a, dtype=torch.long)
        a_embed = self.action_embed(a)
        s_embed = F.relu(self.state_trans(s))
        sa = torch.cat((s_embed, a_embed), dim=1)
        sa = F.relu(self.fc2(sa))
        q = self.fc3(sa)
        return q


def get_action(s, net):
    import random
    if random.uniform(0, 1) < 0.05:
        return random.randint(0, 1)
    max_q, max_a = 1, -1
    for a in range(2):
        a_tensor = torch.tensor([a], dtype=torch.long)
        q = net(s, a_tensor)
        if max_a == -1 or max_q < q:
            max_q, max_a = q, a

    return max_a


env = gym.make('CartPole-v0')
env.reset()
net = Net()

criterion = nn.MSELoss()
optimizer = torch.optim.Adam(net.parameters(), lr=0.001)

for epoch in range(300):
    path = []
    ob = np.array(((0, 0, 0, 0),), dtype=np.float32)
    done = False
    while not done:
        action = get_action(ob, net)
        path.append([ob, [action], 0])
        ob, r, done, info = env.step(action)
        path[-1][-1] = r
        ob = (ob,)
        env.render()
    g = 0
    loss_value = 0
    for all_state in reversed(path):
        g += all_state[2]
        optimizer.zero_grad()
        outputs = net(all_state[0], all_state[1])
        g_tensor = torch.tensor([[g]], dtype=torch.float)
        loss = criterion(outputs, g_tensor)
        loss.backward()
        optimizer.step()
        loss_value += loss.item()
    print('Epoch {}: step={}, loss={}'.format(epoch, len(path), loss_value / len(path)))
    env.reset()
env.close()

