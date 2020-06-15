using System;
using System.Collections.Generic;
using System.Linq;

namespace HelloWorld
{
    public class Hello {
        public static void Main(string[] args)
        {
            var lst = new List<int>() { 1, 2, 3 };
            var lin = lst
                .Select(i => i * 2)
                .ToArray();
            Console.WriteLine("C# working");
        }
    }
}