# Intel2GAS
Convert MASM style inline assembly to AT&T style inline assembly, and output in pure AT&T assembly code or gcc inline assembly code. support x86, x86_64 instructions. It is a brand new replacement to old [intel2gas](http://freecode.com/projects/intel2gas "Old Intel2GAS") project.

Install
-------

> $ git clone https://github.com/skywind3000/Intel2GAS.git Intel2GAS

Convert Assembly in GUI
-----------------------

Run intel2gui.pyw directly, to get into GUI front-end. and convert masm source into AT&T Style (with or without inline mode).

> $ cd Intel2GAS
> 
> $ python intel2gui.pyw

**Convert Without GCC Inline mode** 

![](https://raw.githubusercontent.com/skywind3000/Intel2GAS/master/images/intel2gas_0.png)

**Convert With GCC Inline mode**

![](https://raw.githubusercontent.com/skywind3000/Intel2GAS/master/images/intel2gas_1.png)

**MMX Alpha Blend Demo**

![](https://raw.githubusercontent.com/skywind3000/Intel2GAS/master/images/intel2gas_2.png)


Convert Assembly in Console
---------------------------

> $ cd Intel2GAS
> 
> $ cat demo.asm

```asm
	cld
	mov esi, src
	mov edi, dst
	mov ecx, size
label1:
	mov al, [esi]
	inc al ; calculate
	mov [edi], al
	inc esi
	inc edi
	dec ecx
	jnz label1  ; loop to la
        ret
```

**Convert Without GCC Inline**

> $ python intel2gas.py -m < demo.asm  

```asm
    cld
    mov %0, %esi
    mov %1, %edi
    mov %2, %ecx
label1:
    mov (%esi), %al
    inc %al             //calculate
    mov %al, (%edi)
    inc %esi
    inc %edi
    dec %ecx
    jnz label1          //loop to la
    ret
```

**Convert With GCC Inline** 

> $ python intel2gas.py -m < demo.asm  

```asm
__asm__ __volatile__ (
  "    cld\n"
  "    mov %0, %%esi\n"
  "    mov %1, %%edi\n"
  "    mov %2, %%ecx\n"
  "label1:\n"
  "    mov (%%esi), %%al\n"
  "    inc %%al\n"          //calculate
  "    mov %%al, (%%edi)\n"
  "    inc %%esi\n"
  "    inc %%edi\n"
  "    dec %%ecx\n"
  "    jnz label1\n"        //loop to la
  "    ret\n"
  :
  :"m"(src), "m"(dst), "m"(size)
  :"memory", "esi", "edi", "eax", "ebx", "ecx", "edx"
);
```

