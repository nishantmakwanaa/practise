public class Practise {

    public static void main(String[] args) {

        // 1. Write a Java program to print 'Hello' on screen and then print your name on a separate line.

        System.out.println("Hello");
        System.out.println("Sahil");

        // two sum

        int a = 10;
        int b = 20;
        int sum = a + b;

        System.out.println("Sum of a and b is: " + sum);

        // two sum with array
        int[] nums = {2, 7, 11, 15};
        int target = 9;
        
        for(int i = 0; i < nums.length; i++) {
            for(int j = i + 1; j < nums.length; j++) {
                if(nums[i] + nums[j] == target) {
                    System.out.println("Found two numbers: " + nums[i] + " and " + nums[j]);
                    System.out.println("Indices are: " + i + " and " + j);
                }
            }
        }
    }

  
}
