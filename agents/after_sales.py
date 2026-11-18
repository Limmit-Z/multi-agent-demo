"""Deterministic demonstrations of FAQ and in-memory ticket creation."""
TICKETS = []


def ticket_create(question, user):
    ticket = {'id':f'DEMO-{len(TICKETS)+1:04d}', 'user_id':user['user_id'], 'question':question}
    TICKETS.append(ticket)
    return ticket


def faq_search(question):
    if any(word in question for word in ('退款','退掉','退货')):
        return '请核对购买记录并提交退款申请；具体结果以人工审核为准。'
    if '发票' in question:
        return '请准备订单号和开票信息，提交开票申请。'
    return '请检查激活信息和订单状态；仍有问题可提交演示工单。'


def handle(question, user, previous):
    if '工单' in question:
        ticket = ticket_create(question, user)
        return f"演示工单 {ticket['id']} 已创建，请补充相关情况。"
    return faq_search(question)
