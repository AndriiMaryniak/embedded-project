import matplotlib.pyplot as plt
import numpy as np

categories = ['Unit-тести\n(Бекенд)', 'Інтеграція\n(MQTT)', 'E2E UI\n(Selenium)']
passed = [2, 1, 1]
failed = [2, 1, 2] 
coverage = [95, 85, 70]

x = np.arange(len(categories))
width = 0.35

plt.style.use('seaborn-v0_8-whitegrid')
fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(10, 8.5), sharex=True, gridspec_kw={'height_ratios': [1.8, 1]})
fig.suptitle('Комплексний звіт QA: Аналіз дефектів та покриття коду (Етап 9)', fontsize=16, fontweight='bold', y=0.96)


rects1 = ax1.bar(x - width/2, passed, width, label='Успішні (Реліз)', color='#4CAF50', edgecolor='black', alpha=0.9)
rects2 = ax1.bar(x + width/2, failed, width, label='Знайдені та виправлені баги', color='#F44336', edgecolor='black', alpha=0.9)

ax1.set_ylabel('Кількість', fontsize=12, fontweight='bold')
ax1.set_title('Розподіл результатів тестування', fontsize=13, pad=10)
ax1.set_ylim(0, 4) 

ax1.bar_label(rects1, padding=3, fontsize=12, fontweight='bold', color='#1B5E20')
ax1.bar_label(rects2, padding=3, fontsize=12, fontweight='bold', color='#B71C1C')
ax1.legend(loc='upper right', fontsize=11)


rects3 = ax2.bar(x, coverage, width=0.45, label='Покриття коду (%)', color='#2196F3', edgecolor='black', alpha=0.85)

ax2.set_ylabel('Відсотки (%)', fontsize=12, fontweight='bold', color='#1976D2')
ax2.set_title('Покриття коду', fontsize=13, pad=10)
ax2.set_ylim(0, 115)

ax2.bar_label(rects3, fmt='%d%%', padding=3, fontsize=12, fontweight='bold', color='#0D47A1')
ax2.set_xticks(x)
ax2.set_xticklabels(categories, fontsize=13, fontweight='bold')

plt.tight_layout()
plt.subplots_adjust(top=0.88, hspace=0.15) 
plt.savefig('qa_report_perfect.png', dpi=300, bbox_inches='tight')