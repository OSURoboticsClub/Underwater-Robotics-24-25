library(openintro)
library(tidyverse)
library(broom)

float_data <- read.csv("C:/Users/smith/Downloads/float-testing.txt")

our_float <- float_data %>%
  filter(name == "EX31") %>%
  select(-name)

ggplot(data = our_float, aes(x = time, y = depth)) + 
  geom_point() +
  labs(x = "Time (ms since float power on",
       y = "Depth (m)") 