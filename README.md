# AutoChat

## Supported Features

- 针对微信平台，支持将GUI解析为JSON结构化GUI树并获取截图
- 获取屏幕截图，截图为所有滚动结束后的最终界面
- 支持识别可滚动控件`ListBox`，并将`ListBox`的中的所有条目滚动到可见区域并解析

## TODO

1. 构造`exploration trace`，为LLM提供`domain specific`的app知识
2. 接入云端LLM模型(GPT-4o)
3. 对静动态控件进行分类
4. 对动态控件类型进行抽象汇总

## Vulnerabilities

- 目前可滚动控件仅对`ListBox`类型进行处理，其他类型的可滚动控件暂不支持
