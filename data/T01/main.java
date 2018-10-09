import java.util.Scanner;

class main {
  
  public static void main(String[] args) {
    Scanner reader = new Scanner(System.in);
    
    while (reader.hasNextLine()){
        String name = reader.nextLine();
        System.out.format("Hello, %s!%n", name);
    }
    // String name = reader.nextLine();
    // System.out.format("Hello, %s!%n", name);
  }
}
