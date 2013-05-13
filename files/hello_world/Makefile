# Makefile for hello_world

TARGET := hello_world

CC = gcc

SRCS := hello_world.c
OBJS := $(SRCS:%.c=%.o)

all: $(TARGET)

$(TARGET): $(OBJS)
	$(CC) -o $@ $<

clean:
	rm -f $(OBJS)

distclean: clean
	rm -f $(TARGET)

# EOF
