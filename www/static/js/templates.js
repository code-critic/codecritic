String.prototype.format = function () {
    var formatted = this;
    for (var i = 0; i < arguments.length; i++) {
        var regexp = new RegExp('\\{' + i + '\\}', 'gi');
        formatted = formatted.replace(regexp, arguments[i]);
    }
    return formatted;
};
class Globals {
    static initEnv() {
        var URL = `${location.protocol}//${document.domain}:${location.port}`;
        this.env = nunjucks.configure(URL, {
            autoescape: true,
        });
        this.env.addFilter('toFixed', (num, digits) => {
            return parseFloat(num).toFixed(digits || 2);
        });
        this.env.addFilter('pad', (n, w = 2, z = '0') => {
            let m = n.toString();
            return m.length >= w ? m : new Array(w - m.length + 1).join(z) + m;
        });
        this.env.addFilter('cut', (str, digits) => {
            return str.substring(0, digits || 8);
        });
        this.env.addGlobal('inArray', function (value, arr) {
            return arr.includes(value);
        });
        this.env.addFilter('toFixed', function (num, digits) {
            return parseFloat(num).toFixed(digits);
        });
        window.toastr.options.progressBar = true;
    }
}
class Templates {
    static render(template, data) {
        var templateUrl = `static/templates/${template}.njk`;
        var njk = this.templates[template];
        if (njk) {
            return njk.render(data);
        }
        else {
            this.templates[template] = Globals.env.getTemplate(templateUrl, true);
            return this.templates[template].render(data);
        }
    }
}
Templates.templates = {};
class LangExamples {
}
LangExamples.examples = {
    'PY-367': `# python 3.5+ example
import sys

for line in sys.stdin:
    i = int(str(line).strip())
    if i == 42:
        break
    else:
        print(i)`,
    'PY-276': `# python 2.7 example
import sys

for line in sys.stdin:
    i = int(str(line).strip())
    if i == 42:
        break
    else:
        print i`,
    'CPP': `// C++ example
#include <iostream> 
using namespace std; 
  
int main() 
{ 
  
    // Declare the variables 
    int num; 
  
    // Input the integer 
    cout << "Enter the integer: "; 
    cin >> num; 
  
    // Display the integer 
    cout << "Entered integer is: " << num; 
  
    return 0; 
}`,
    'JAVA': `// JAVA example
import java.util.Scanner;

public class MatrixReader {
    public static void main(String[] args) {
        Scanner input = new Scanner(System.in);
        while (input.hasNext()) {
            System.out.print(input.nextLine());
        }
    }
}`,
    'CS': `// C# example
using System;
 
namespace Sample
{
	class Test
	{
		public static void Main(string[] args)
		{
			string testString;
			Console.Write("Enter a string - ");
			testString = Console.ReadLine();
			Console.WriteLine("You entered '{0}'", testString);
		}
	}
}`,
    'C': `// C example
#include <stdio.h>   

int main(void)
{
  int i;
  char name[BUFSIZ];
  
  printf ("Input a number: ");
  scanf("%d", &i);
  
  printf("Enter your name: ");
  fgets(name, BUFSIZ, stdin);
  
  printf ("Hello %s, your number was %d\n", name, i);
  
  return(0);
}`,
};
//# sourceMappingURL=templates.js.map
